"""
LoRA Fine-tuning Module
Handles model loading, LoRA/QLoRA training, and weight management
"""

import os
import json
import torch
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from peft.utils import prepare_model_for_kbit_training as _prepare_qloar
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset


@dataclass
class LoRAConfig:
    """LoRA configuration"""
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"])
    bias: str = "none"
    task_type: str = "CAUSAL_LM"


@dataclass
class QLoRAConfig:
    """QLoRA configuration for 4-bit quantization"""
    enabled: bool = True
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_quant_type: str = "nf4"


@dataclass
class TrainingConfig:
    """Training configuration"""
    output_dir: str = "./output/lora_train"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_steps: int = 10
    logging_steps: int = 10
    save_steps: int = 50
    eval_steps: int = 50
    save_total_limit: int = 2


class LoRATrainer:
    """LoRA fine-tuning trainer for ad copy generation"""

    def __init__(
        self,
        base_model_path: str = "Qwen/Qwen2.5-0.5B",
        cache_dir: str = "./models",
        device: str = "auto",
        config_path: Optional[str] = None
    ):
        self.base_model_path = base_model_path
        self.cache_dir = cache_dir
        self.device = device
        self.model = None
        self.tokenizer = None
        self.peft_model = None
        self.trainer = None

        # Load config from file if provided
        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                self.lora_config = LoRAConfig(**config.get("lora", {}))
                self.qlora_config = QLoRAConfig(**config.get("qlora", {}))
                self.training_config = TrainingConfig(**config.get("training", {}))
        else:
            self.lora_config = LoRAConfig()
            self.qlora_config = QLoRAConfig()
            self.training_config = TrainingConfig()

    def load_model(self, quantize: bool = False):
        """Load base model and tokenizer"""
        print(f"Loading base model: {self.base_model_path}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_path,
            cache_dir=self.cache_dir,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with optional quantization
        if quantize and self.qlora_config.enabled:
            print("Using QLoRA (4-bit quantization)")
            from transformers import BitsAndBytesConfig

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=self.qlora_config.load_in_4bit,
                bnb_4bit_compute_dtype=getattr(torch, self.qlora_config.bnb_4bit_compute_dtype),
                bnb_4bit_use_double_quant=self.qlora_config.bnb_4bit_use_double_quant,
                bnb_4bit_quant_type=self.qlora_config.bnb_4bit_quant_type,
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                cache_dir=self.cache_dir,
                quantization_config=bnb_config,
                device_map=self.device,
                trust_remote_code=True
            )
            self.model = prepare_model_for_kbit_training(self.model)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                cache_dir=self.cache_dir,
                device_map=self.device,
                torch_dtype=torch.float16,
                trust_remote_code=True
            )

        print("Model loaded successfully")
        return self.model, self.tokenizer

    def setup_lora(self):
        """Setup LoRA adapter on the model"""
        lora_config = LoraConfig(
            r=self.lora_config.r,
            lora_alpha=self.lora_config.lora_alpha,
            lora_dropout=self.lora_config.lora_dropout,
            target_modules=self.lora_config.target_modules,
            bias=self.lora_config.bias,
            task_type=self.lora_config.task_type,
        )

        self.peft_model = get_peft_model(self.model, lora_config)

        # Print trainable parameters
        self.peft_model.print_trainable_parameters()

        return self.peft_model

    def prepare_dataset(self, records: List[Dict]) -> Dataset:
        """Prepare dataset for training"""
        def format_prompt(record):
            """Format a single record as training prompt"""
            source = record.get("source_content", "")
            target = record.get("target_content", "")

            prompt = f"""请将以下低CTR广告文案优化为高CTR文案：

低CTR文案：{source}

高CTR优化文案：{target}"""
            return prompt

        texts = [format_prompt(r) for r in records]

        # Tokenize
        def tokenize_function(examples):
            result = self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=512,
                padding="max_length"
            )
            result["labels"] = result["input_ids"].copy()
            return result

        dataset = Dataset.from_dict({"text": texts})
        dataset = dataset.map(tokenize_function, batched=True)

        return dataset

    def train(
        self,
        train_records: List[Dict],
        val_records: Optional[List[Dict]] = None,
        output_dir: Optional[str] = None,
        callbacks: Optional[List] = None
    ) -> Dict:
        """Train the model"""
        if output_dir:
            self.training_config.output_dir = output_dir

        # Prepare datasets
        train_dataset = self.prepare_dataset(train_records)

        if val_records:
            val_dataset = self.prepare_dataset(val_records)
        else:
            val_dataset = None

        # Setup training arguments
        training_args = TrainingArguments(
            output_dir=self.training_config.output_dir,
            num_train_epochs=self.training_config.num_train_epochs,
            per_device_train_batch_size=self.training_config.per_device_train_batch_size,
            gradient_accumulation_steps=self.training_config.gradient_accumulation_steps,
            learning_rate=self.training_config.learning_rate,
            warmup_steps=self.training_config.warmup_steps,
            logging_steps=self.training_config.logging_steps,
            save_steps=self.training_config.save_steps,
            eval_steps=self.training_config.eval_steps,
            save_total_limit=self.training_config.save_total_limit,
            eval_strategy="steps" if val_dataset else "no",
            save_strategy="steps",
            load_best_model_at_end=True if val_dataset else False,
            fp16=True,
            report_to="none",
            logging_dir=f"{self.training_config.output_dir}/logs",
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # Causal LM
        )

        # Create trainer
        self.trainer = Trainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            callbacks=callbacks,
        )

        # Train
        print("Starting training...")
        train_result = self.trainer.train()

        # Save model
        self.peft_model.save_pretrained(self.training_config.output_dir)

        return {
            "train_loss": train_result.training_loss,
            "output_dir": self.training_config.output_dir,
            "train_samples": len(train_records),
            "eval_samples": len(val_records) if val_records else 0,
        }

    def merge_weights(self, output_path: Optional[str] = None) -> str:
        """Merge LoRA weights with base model and save"""
        if output_path is None:
            output_path = f"{self.training_config.output_dir}/merged_model"

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Merge weights
        merged_model = self.peft_model.merge_and_unload()
        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

        print(f"Merged model saved to: {output_path}")
        return str(output_path)


class TrainingProgressCallback:
    """Callback to track training progress"""

    def __init__(self):
        self.history = {
            "train_loss": [],
            "eval_loss": [],
            "step": []
        }

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            if "loss" in logs:
                self.history["train_loss"].append(logs["loss"])
                self.history["step"].append(state.global_step)
            if "eval_loss" in logs:
                self.history["eval_loss"].append(logs["eval_loss"])


if __name__ == "__main__":
    from utils.hardware_detect import detect_hardware

    mode = detect_hardware()
    print(f"Detected mode: {mode}")

    # Initialize trainer
    trainer = LoRATrainer(
        base_model_path="Qwen/Qwen2.5-0.5B",
        config_path="config.yaml"
    )

    # Load model
    quantize = mode in ["QLoRA", "CPU"]
    trainer.load_model(quantize=quantize)

    # Setup LoRA
    trainer.setup_lora()

    print("LoRA trainer ready. Call trainer.train() with your dataset.")
