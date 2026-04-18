"""
Dataset Processing Module
Handles upload, cleaning, splitting, and format conversion for paired ad copy data
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DatasetConfig:
    """Dataset processing configuration"""
    supported_formats: List[str] = None
    required_fields: List[str] = None
    default_split_ratio: float = 0.8

    def __post_init__(self):
        self.supported_formats = self.supported_formats or [".json", ".jsonl"]
        self.required_fields = self.required_fields or ["source_content", "target_content"]


class DatasetProcessor:
    """Process and validate paired ad copy datasets"""

    # Common violation words in Chinese advertising
    VIOLATION_WORDS = [
        "最", "第一", "国家级", "最高级", "极品", "绝佳",
        "绝对", "永久", "极致", "顶级", "至尊", "独家",
        "唯一", "首选", "绝佳", "完美", "无敌"
    ]

    def __init__(self, config: Optional[DatasetConfig] = None):
        self.config = config or DatasetConfig()

    def load_dataset(self, file_path: str) -> List[Dict]:
        """Load dataset from JSON or JSONL file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        if path.suffix == ".jsonl":
            with open(path, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f]
        elif path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")

    def validate_record(self, record: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a single record"""
        for field in self.config.required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"

        if not record.get("source_content", "").strip():
            return False, "Empty source_content"

        if not record.get("target_content", "").strip():
            return False, "Empty target_content"

        return True, None

    def clean_record(self, record: Dict) -> Optional[Dict]:
        """Clean a single record - returns None if should be filtered"""
        source = record.get("source_content", "")
        target = record.get("target_content", "")

        # Check for violation words
        for word in self.VIOLATION_WORDS:
            if word in source or word in target:
                return None  # Filter out

        # Basic text cleaning
        source = self._clean_text(source)
        target = self._clean_text(target)

        if len(source) < 5 or len(target) < 5:
            return None

        record["source_content"] = source
        record["target_content"] = target

        return record

    def _clean_text(self, text: str) -> str:
        """Clean text - remove extra spaces, normalize punctuation"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove common typos
        text = text.strip()
        return text

    def remove_duplicates(self, records: List[Dict]) -> Tuple[List[Dict], int]:
        """Remove duplicate records based on content hash"""
        seen_hashes = set()
        unique_records = []
        duplicate_count = 0

        for record in records:
            content = record.get("source_content", "") + "|" + record.get("target_content", "")
            content_hash = hashlib.md5(content.encode()).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_records.append(record)
            else:
                duplicate_count += 1

        return unique_records, duplicate_count

    def clean_dataset(self, records: List[Dict]) -> Dict[str, any]:
        """
        Clean entire dataset
        Returns: {
            "records": cleaned records,
            "stats": {
                "total": int,
                "removed_duplicates": int,
                "removed_violations": int,
                "removed_empty": int,
                "valid": int
            }
        }
        """
        initial_count = len(records)

        # Remove duplicates
        records, dup_count = self.remove_duplicates(records)

        # Clean each record
        cleaned = []
        violation_count = 0
        empty_count = 0

        for record in records:
            valid, error = self.validate_record(record)
            if not valid:
                empty_count += 1
                continue

            cleaned_record = self.clean_record(record)
            if cleaned_record is None:
                violation_count += 1
                continue

            cleaned.append(cleaned_record)

        return {
            "records": cleaned,
            "stats": {
                "total": initial_count,
                "removed_duplicates": dup_count,
                "removed_violations": violation_count,
                "removed_empty": empty_count,
                "valid": len(cleaned)
            }
        }

    def split_dataset(
        self,
        records: List[Dict],
        split_ratio: float = 0.8,
        seed: int = 42
    ) -> Tuple[List[Dict], List[Dict]]:
        """Split dataset into train and validation sets"""
        import random
        random.seed(seed)

        shuffled = records.copy()
        random.shuffle(shuffled)

        split_idx = int(len(shuffled) * split_ratio)
        train_records = shuffled[:split_idx]
        val_records = shuffled[split_idx:]

        return train_records, val_records

    def convert_to_chat_format(
        self,
        records: List[Dict],
        source_field: str = "source_content",
        target_field: str = "target_content"
    ) -> List[Dict]:
        """
        Convert records to chat messages format for LLM training
        Format: {"messages": [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}
        """
        chat_records = []

        for record in records:
            messages = [
                {"role": "user", "content": f"请将以下低CTR广告文案优化为高CTR文案：\n{record.get(source_field, '')}"},
                {"role": "assistant", "content": record.get(target_field, "")}
            ]

            chat_record = {
                "messages": messages,
                "industry_tag": record.get("industry_tag", "unknown"),
                "copy_type": record.get("copy_type", "unknown")
            }
            chat_records.append(chat_record)

        return chat_records

    def save_dataset(
        self,
        records: List[Dict],
        output_path: str,
        format: str = "jsonl"
    ) -> Path:
        """Save processed dataset to file"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "jsonl":
            with open(path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)

        return path


class DatasetStats:
    """Calculate and display dataset statistics"""

    @staticmethod
    def get_stats(records: List[Dict]) -> Dict:
        """Calculate dataset statistics"""
        industries = {}
        copy_types = {}
        source_lengths = []
        target_lengths = []

        for record in records:
            industry = record.get("industry_tag", "unknown")
            copy_type = record.get("copy_type", "unknown")

            industries[industry] = industries.get(industry, 0) + 1
            copy_types[copy_type] = copy_types.get(copy_type, 0) + 1

            source_lengths.append(len(record.get("source_content", "")))
            target_lengths.append(len(record.get("target_content", "")))

        return {
            "total": len(records),
            "by_industry": industries,
            "by_copy_type": copy_types,
            "source_avg_length": sum(source_lengths) / len(source_lengths) if source_lengths else 0,
            "target_avg_length": sum(target_lengths) / len(target_lengths) if target_lengths else 0,
        }


if __name__ == "__main__":
    # Test with mock data
    processor = DatasetProcessor()

    # Load mock data
    records = processor.load_dataset("mock_dataset.jsonl")
    print(f"Loaded {len(records)} records")

    # Clean
    result = processor.clean_dataset(records)
    print(f"Cleaned: {result['stats']}")

    # Split
    train, val = processor.split_dataset(result["records"])
    print(f"Train: {len(train)}, Val: {len(val)}")

    # Stats
    stats = DatasetStats.get_stats(train)
    print(f"Train stats: {stats}")
