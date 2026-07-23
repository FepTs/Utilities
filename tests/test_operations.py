from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path

from yolo_utils.common import UtilityError
from yolo_utils.converters import convert_json_to_yolo
from yolo_utils.files import matching_files, rename_files
from yolo_utils.labels import clean_labels, generate_uniform_labels, merge_labels


class OperationTests(unittest.TestCase):
    def test_generation_module_has_no_import_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            before = set(Path(temporary).iterdir())
            importlib.import_module("src.GenerationLabels")
            self.assertEqual(set(Path(temporary).iterdir()), before)

    def test_generate_uniform_labels_filters_non_images(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            images = root / "images"
            images.mkdir()
            (images / "one.jpg").write_bytes(b"image")
            (images / "notes.md").write_text("not an image", encoding="utf-8")

            report = generate_uniform_labels(images, root / "labels", "0 0.5 0.5 1 1")

            self.assertEqual(report.changed, 1)
            self.assertTrue((root / "labels" / "one.txt").is_file())
            self.assertFalse((root / "labels" / "notes.txt").exists())

    def test_clean_labels_validates_every_file_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            labels = Path(temporary)
            good = labels / "a.txt"
            bad = labels / "b.txt"
            original = "2 0.5 0.5 0.2 0.2\n"
            good.write_text(original, encoding="utf-8")
            bad.write_text("broken line\n", encoding="utf-8")

            with self.assertRaises(UtilityError):
                clean_labels(labels, [2])

            self.assertEqual(good.read_text("utf-8"), original)

    def test_clean_labels_remaps_classes_contiguously(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            labels = Path(temporary)
            target = labels / "a.txt"
            target.write_text(
                "0 0.5 0.5 0.2 0.2\n2 0.4 0.4 0.1 0.1\n3 0.3 0.3 0.1 0.1\n",
                encoding="utf-8",
            )
            clean_labels(labels, [0, 2])
            self.assertEqual(
                target.read_text("utf-8"),
                "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.1 0.1\n",
            )

    def test_rename_handles_existing_target_names_without_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "00001.jpg").write_text("first", encoding="utf-8")
            (folder / "z.jpg").write_text("second", encoding="utf-8")

            rename_files(folder, "jpg", 1)

            self.assertEqual((folder / "00001.jpg").read_text("utf-8"), "first")
            self.assertEqual((folder / "00002.jpg").read_text("utf-8"), "second")

    def test_batch_delete_requires_a_non_empty_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "important.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(UtilityError, "不能为空"):
                matching_files(folder, "", ".txt")

    def test_json_to_yolo_has_no_legacy_minus_one_offset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "sample.json"
            output = root / "sample.txt"
            source.write_text(
                json.dumps(
                    {
                        "imageWidth": 100,
                        "imageHeight": 100,
                        "shapes": [
                            {
                                "label": "car",
                                "shape_type": "rectangle",
                                "points": [[10, 20], [30, 40]],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            convert_json_to_yolo(source, output, {"car": 0})

            self.assertEqual(output.read_text("utf-8"), "0 0.200000 0.300000 0.200000 0.200000\n")

    def test_merge_inserts_exactly_one_separator_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            source = root / "source"
            target.mkdir()
            source.mkdir()
            (target / "a.txt").write_text("0 0.5 0.5 0.2 0.2", encoding="utf-8")
            (source / "a.txt").write_text("1 0.4 0.4 0.1 0.1\n", encoding="utf-8")

            merge_labels(target, source)

            self.assertEqual(
                (target / "a.txt").read_text("utf-8"),
                "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.1 0.1\n",
            )


if __name__ == "__main__":
    unittest.main()
