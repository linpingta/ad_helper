"""
Copy Generation Module
Handles inference and batch generation with BLEU/ROUGE evaluation
"""

import json
import torch
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


@dataclass
class GenerationConfig:
    """Generation configuration"""
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True


class CopyGenerator:
    """Generate ad copy using fine-tuned LoRA model"""

    def __init__(
        self,
        model_path: str,
        lora_path: Optional[str] = None,
        device: str = "auto",
        tokenizer_path: Optional[str] = None
    ):
        self.model_path = model_path
        self.lora_path = lora_path
        self.device = device if device != "auto" else "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer_path = tokenizer_path or model_path

        self.model = None
        self.tokenizer = None
        self.generation_config = GenerationConfig()

    def load_model(self):
        """Load model and optional LoRA adapter"""
        print(f"Loading model from: {self.model_path}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.tokenizer_path,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map=self.device,
            torch_dtype=torch.float16,
            trust_remote_code=True
        )

        # Load LoRA adapter if provided
        if self.lora_path and Path(self.lora_path).exists():
            print(f"Loading LoRA adapter from: {self.lora_path}")
            self.model = PeftModel.from_pretrained(self.model, self.lora_path)

        self.model.eval()
        print("Model loaded successfully")

        return self.model, self.tokenizer

    def generate_single(
        self,
        source_content: str,
        industry_tag: Optional[str] = None,
        copy_type: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> Dict:
        """Generate a single ad copy"""
        if config is None:
            config = self.generation_config

        # Build prompt
        prompt = self._build_prompt(source_content, industry_tag, copy_type)

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                repetition_penalty=config.repetition_penalty,
                do_sample=config.do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract response (remove the prompt)
        response = generated_text[len(prompt):].strip()

        return {
            "source_content": source_content,
            "generated_content": response,
            "industry_tag": industry_tag,
            "copy_type": copy_type,
            "prompt": prompt
        }

    def generate_batch(
        self,
        records: List[Dict],
        config: Optional[GenerationConfig] = None,
        show_progress: bool = True
    ) -> List[Dict]:
        """Generate ad copies for a batch of records"""
        results = []

        iterator = records
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(records, desc="Generating")
            except ImportError:
                pass

        for record in iterator:
            result = self.generate_single(
                source_content=record.get("source_content", ""),
                industry_tag=record.get("industry_tag"),
                copy_type=record.get("copy_type"),
                config=config
            )
            results.append(result)

        return results

    def _build_prompt(
        self,
        source_content: str,
        industry_tag: Optional[str] = None,
        copy_type: Optional[str] = None
    ) -> str:
        """Build prompt for generation"""
        industry_hint = ""
        if industry_tag:
            industry_names = {
                "industry_beauty": "美妆",
                "industry_fashion": "服装",
                "industry_game": "游戏"
            }
            industry_hint = f"（行业：{industry_names.get(industry_tag, industry_tag)}）"

        copy_type_hint = ""
        if copy_type:
            copy_type_names = {
                "title": "标题",
                "detail": "详情页",
                "banner": "Banner",
                "short_video": "短视频"
            }
            copy_type_hint = f"，类型：{copy_type_names.get(copy_type, copy_type)}"

        prompt = f"""请将以下低CTR广告文案优化为高CTR文案{industry_hint}{copy_type_hint}：

低CTR文案：{source_content}

高CTR优化文案："""

        return prompt

    def save_results(self, results: List[Dict], output_path: str, format: str = "jsonl"):
        """Save generation results to file"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "jsonl":
            with open(path, "w", encoding="utf-8") as f:
                for result in results:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Results saved to: {path}")


class Evaluator:
    """Evaluate generated copies using BLEU and ROUGE metrics"""

    def __init__(self):
        self._init_metrics()

    def _init_metrics(self):
        """Initialize metrics computation"""
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            from rouge_score import rouge_scorer
            self.bleu_func = sentence_bleu
            self.smoothing = SmoothingFunction().method1
            self.rouge_scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
            self.metrics_available = True
        except ImportError:
            print("Warning: nltk or rouge-score not installed. Using placeholder metrics.")
            self.metrics_available = False

    def compute_bleu(self, reference: str, hypothesis: str) -> float:
        """Compute BLEU score"""
        if not self.metrics_available:
            return 0.0

        ref_tokens = reference.split()
        hyp_tokens = hypothesis.split()

        if len(hyp_tokens) == 0 or len(ref_tokens) == 0:
            return 0.0

        try:
            return self.bleu_func([ref_tokens], hyp_tokens, smoothing_function=self.smoothing)
        except:
            return 0.0

    def compute_rouge_l(self, reference: str, hypothesis: str) -> float:
        """Compute ROUGE-L score"""
        if not self.metrics_available:
            return 0.0

        try:
            scores = self.rouge_scorer.score(reference, hypothesis)
            return scores['rougeL'].fmeasure
        except:
            return 0.0

    def evaluate_batch(
        self,
        results: List[Dict],
        reference_field: str = "target_content"
    ) -> Dict:
        """Evaluate a batch of generated results"""
        bleu_scores = []
        rouge_scores = []

        for result in results:
            reference = result.get(reference_field, "")
            hypothesis = result.get("generated_content", "")

            bleu = self.compute_bleu(reference, hypothesis)
            rouge = self.compute_rouge_l(reference, hypothesis)

            bleu_scores.append(bleu)
            rouge_scores.append(rouge)

        return {
            "bleu": {
                "mean": sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0,
                "scores": bleu_scores
            },
            "rouge_l": {
                "mean": sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0,
                "scores": rouge_scores
            },
            "sample_count": len(results)
        }


if __name__ == "__main__":
    print("CopyGenerator module loaded. Use with a fine-tuned model.")
