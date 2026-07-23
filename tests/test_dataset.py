from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from yolo_utils.common import UtilityError
from yolo_utils.dataset import split_classification_dataset, split_detection_dataset


class DetectionSplitTests(unittest.TestCase):
    def make_dataset(self, root: Path, count: int = 10) -> Path:
        dataset = root / "dataset"
        images = dataset / "images"
        labels = dataset / "labels"
        images.mkdir(parents=True)
        labels.mkdir()
        for number in range(1, count + 1):
            (images / f"{number}.jpg").write_bytes(f"image-{number}".encode())
            (labels / f"{number}.txt").write_text(
                f"0 0.5 0.5 0.{number} 0.{number}\n", encoding="utf-8"
            )
        return dataset

    def assert_pairs_match(self, output: Path, subset: str) -> None:
        image_stems = {path.stem for path in (output / subset / "images").iterdir()}
        label_stems = {path.stem for path in (output / subset / "labels").iterdir()}
        self.assertEqual(image_stems, label_stems)

    def test_split_keeps_each_image_with_its_label(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.make_dataset(root)
            output = root / "output"

            report = split_detection_dataset(dataset, output, 0.7, seed=7)

            self.assertEqual(report.train_count, 7)
            self.assertEqual(report.validation_count, 3)
            self.assert_pairs_match(output, "train")
            self.assert_pairs_match(output, "val")
            train = {path.stem for path in (output / "train" / "images").iterdir()}
            validation = {path.stem for path in (output / "val" / "images").iterdir()}
            self.assertFalse(train & validation)
            self.assertEqual(train | validation, {str(number) for number in range(1, 11)})

    def test_seed_reproduces_the_exact_split(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.make_dataset(root)
            first = root / "first"
            second = root / "second"
            split_detection_dataset(dataset, first, 0.7, seed=123)
            split_detection_dataset(dataset, second, 0.7, seed=123)
            first_manifest = json.loads((first / "split_manifest.json").read_text("utf-8"))
            second_manifest = json.loads((second / "split_manifest.json").read_text("utf-8"))
            self.assertEqual(first_manifest["subsets"], second_manifest["subsets"])

    def test_unmatched_files_are_reported_and_not_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.make_dataset(root, count=3)
            (dataset / "images" / "missing.jpg").write_bytes(b"missing")
            (dataset / "labels" / "orphan.txt").write_text("", encoding="utf-8")

            report = split_detection_dataset(dataset, root / "output", 0.5)

            self.assertEqual(report.skipped_images, ("missing.jpg",))
            self.assertEqual(report.orphan_labels, ("orphan.txt",))

    def test_duplicate_image_stems_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.make_dataset(root, count=2)
            (dataset / "images" / "1.png").write_bytes(b"duplicate")
            with self.assertRaisesRegex(UtilityError, "同名"):
                split_detection_dataset(dataset, root / "output", 0.5)

    def test_non_empty_output_is_never_modified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.make_dataset(root, count=2)
            output = root / "output"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(UtilityError, "必须为空"):
                split_detection_dataset(dataset, output, 0.5)
            self.assertEqual(marker.read_text("utf-8"), "keep")

    def test_output_cannot_be_nested_inside_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.make_dataset(root, count=2)
            with self.assertRaisesRegex(UtilityError, "不能位于输入目录内部"):
                split_detection_dataset(dataset, dataset / "output", 0.5)

    def test_classification_split_preserves_each_class(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = root / "classification"
            for class_name in ("cats", "dogs"):
                class_dir = dataset / class_name
                class_dir.mkdir(parents=True)
                for number in range(4):
                    (class_dir / f"{number}.jpg").write_bytes(b"image")

            report = split_classification_dataset(dataset, root / "output", 0.5)

            self.assertEqual(report.train_count, 4)
            self.assertEqual(report.validation_count, 4)
            for subset in ("train", "val"):
                for class_name in ("cats", "dogs"):
                    self.assertEqual(
                        len(list((root / "output" / subset / class_name).iterdir())), 2
                    )


if __name__ == "__main__":
    unittest.main()
