import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

FAST_SCNN_ROOT = (
    PROJECT_ROOT
    / "ai_engine"
    / "segmentation"
    / "Fast-SCNN-pytorch"
)

WEIGHTS_FOLDER = (
    FAST_SCNN_ROOT
    / "weights"
)


# ============================================================
# FAST-SCNN IMPORT PATH
# ============================================================

if str(FAST_SCNN_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(FAST_SCNN_ROOT),
    )


from models.fast_scnn import get_fast_scnn


# ============================================================
# SEGMENTATION SERVICE
# ============================================================

class SegmentationService:

    # Cityscapes class IDs
    ROAD_CLASS = 0
    SIDEWALK_CLASS = 1


    def __init__(self):

        print(
            "Loading Fast-SCNN segmentation model..."
        )

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )


        # ----------------------------------------------------
        # IMAGE TRANSFORM
        # ----------------------------------------------------

        self.transform = transforms.Compose([

            transforms.ToTensor(),

            transforms.Normalize(
                mean=[
                    0.485,
                    0.456,
                    0.406,
                ],
                std=[
                    0.229,
                    0.224,
                    0.225,
                ],
            ),

        ])


        # ----------------------------------------------------
        # LOAD MODEL
        # ----------------------------------------------------

        self.model = get_fast_scnn(

            "citys",

            pretrained=True,

            root=str(
                WEIGHTS_FOLDER
            ),

            map_cpu=(
                self.device.type
                == "cpu"
            ),

        ).to(
            self.device
        )


        self.model.eval()


        print(
            f"Fast-SCNN ready on {self.device}"
        )


    # ========================================================
    # CALCULATE SAFE MODEL SIZE
    # ========================================================

    def calculate_safe_size(
        self,
        width,
        height,
    ):

        """
        Fast-SCNN contains multiple downsampling and
        upsampling stages.

        Input dimensions are converted to values divisible
        by 32 to avoid incompatible feature-map sizes.
        """

        safe_width = (
            width // 32
        ) * 32

        safe_height = (
            height // 32
        ) * 32


        safe_width = max(
            safe_width,
            32,
        )

        safe_height = max(
            safe_height,
            32,
        )


        return (
            safe_width,
            safe_height,
        )


    # ========================================================
    # SEGMENT IMAGE
    # ========================================================

    def segment_image(
        self,
        image_path,
    ):

        # ----------------------------------------------------
        # LOAD IMAGE
        # ----------------------------------------------------

        image = Image.open(
            image_path
        ).convert(
            "RGB"
        )


        original_width, original_height = (
            image.size
        )


        # ----------------------------------------------------
        # CALCULATE SAFE INPUT SIZE
        # ----------------------------------------------------

        safe_width, safe_height = (
            self.calculate_safe_size(
                width=original_width,
                height=original_height,
            )
        )


        # ----------------------------------------------------
        # RESIZE IMAGE FOR FAST-SCNN
        # ----------------------------------------------------

        resized_image = image.resize(

            (
                safe_width,
                safe_height,
            ),

            Image.Resampling.BILINEAR,

        )


        # ----------------------------------------------------
        # PREPROCESS IMAGE
        # ----------------------------------------------------

        input_tensor = (

            self.transform(
                resized_image
            )

            .unsqueeze(0)

            .to(
                self.device
            )
        )


        # ----------------------------------------------------
        # MODEL INFERENCE
        # ----------------------------------------------------

        with torch.no_grad():

            outputs = self.model(
                input_tensor
            )


        # Some Fast-SCNN implementations return
        # a tuple or list of tensors.

        if isinstance(
            outputs,
            (tuple, list),
        ):

            main_output = outputs[0]

        else:

            main_output = outputs


        # ----------------------------------------------------
        # CLASS PREDICTION
        # ----------------------------------------------------

        prediction = torch.argmax(

            main_output,

            dim=1,

        )


        mask = (

            prediction

            .squeeze(0)

            .cpu()

            .numpy()

            .astype(
                np.uint8
            )
        )


        # ----------------------------------------------------
        # RESTORE MASK TO ORIGINAL IMAGE SIZE
        # ----------------------------------------------------

        mask_image = Image.fromarray(
            mask
        )


        mask_image = mask_image.resize(

            (
                original_width,
                original_height,
            ),

            Image.Resampling.NEAREST,

        )


        mask = np.array(
            mask_image,
            dtype=np.uint8,
        )


        # ----------------------------------------------------
        # WALKABILITY ANALYSIS
        # ----------------------------------------------------

        walkability = (
            self.analyze_walkable_path(
                mask
            )
        )


        return {

            "mask": mask,

            "image_width": (
                original_width
            ),

            "image_height": (
                original_height
            ),

            "model_input_width": (
                safe_width
            ),

            "model_input_height": (
                safe_height
            ),

            "walkability": (
                walkability
            ),
        }


    # ========================================================
    # ANALYZE WALKABLE PATH
    # ========================================================

    def analyze_walkable_path(
        self,
        mask,
    ):

        # ----------------------------------------------------
        # VALIDATE MASK
        # ----------------------------------------------------

        if not isinstance(
            mask,
            np.ndarray,
        ):

            raise TypeError(
                "Segmentation mask must be a NumPy array."
            )


        if mask.ndim != 2:

            raise ValueError(
                "Segmentation mask must be a 2D class map."
            )


        height, width = (
            mask.shape
        )


        # ----------------------------------------------------
        # NEARBY WALKING REGION
        # ----------------------------------------------------

        # Focus on lower 45% of the image because this
        # represents the nearby walking area.

        start_y = int(
            height * 0.55
        )


        path_region = mask[
            start_y:height,
            :
        ]


        region_height, region_width = (
            path_region.shape
        )


        # ----------------------------------------------------
        # EMPTY REGION PROTECTION
        # ----------------------------------------------------

        if (
            region_height == 0
            or region_width == 0
        ):

            return {

                "left_walkable_percent": 0.0,

                "center_walkable_percent": 0.0,

                "right_walkable_percent": 0.0,

                "safest_direction": "unknown",

                "path_status": (
                    "INVALID_PATH_REGION"
                ),
            }


        third = max(
            region_width // 3,
            1,
        )


        # ----------------------------------------------------
        # SPLIT INTO LEFT, CENTER, RIGHT
        # ----------------------------------------------------

        left_region = path_region[
            :,
            0:third
        ]


        center_region = path_region[
            :,
            third:third * 2
        ]


        right_region = path_region[
            :,
            third * 2:region_width
        ]


        # ----------------------------------------------------
        # CALCULATE WALKABILITY SCORES
        # ----------------------------------------------------

        left_score = (
            self.calculate_walkable_score(
                left_region
            )
        )


        center_score = (
            self.calculate_walkable_score(
                center_region
            )
        )


        right_score = (
            self.calculate_walkable_score(
                right_region
            )
        )


        scores = {

            "left": left_score,

            "center": center_score,

            "right": right_score,

        }


        # ----------------------------------------------------
        # DETERMINE PATH STATUS
        # ----------------------------------------------------

        max_score = max(
            scores.values()
        )


        if max_score <= 0.0:

            safest_direction = "unknown"

            path_status = (
                "NO_WALKABLE_CLASS_DETECTED"
            )

        else:

            safest_direction = max(
                scores,
                key=scores.get,
            )

            path_status = "ANALYZED"


        # ----------------------------------------------------
        # RETURN WALKABILITY RESULT
        # ----------------------------------------------------

        return {

            "left_walkable_percent": (
                left_score
            ),

            "center_walkable_percent": (
                center_score
            ),

            "right_walkable_percent": (
                right_score
            ),

            "safest_direction": (
                safest_direction
            ),

            "path_status": (
                path_status
            ),
        }


    # ========================================================
    # CALCULATE WALKABILITY SCORE
    # ========================================================

    def calculate_walkable_score(
        self,
        region,
    ):

        if region.size == 0:

            return 0.0


        # ----------------------------------------------------
        # ROAD PIXELS
        # ----------------------------------------------------

        road_pixels = np.sum(

            region
            == self.ROAD_CLASS

        )


        # ----------------------------------------------------
        # SIDEWALK PIXELS
        # ----------------------------------------------------

        sidewalk_pixels = np.sum(

            region
            == self.SIDEWALK_CLASS

        )


        # ----------------------------------------------------
        # TOTAL WALKABLE PIXELS
        # ----------------------------------------------------

        walkable_pixels = (

            road_pixels

            + sidewalk_pixels

        )


        percentage = (

            walkable_pixels

            / region.size

        ) * 100.0


        return round(

            float(
                percentage
            ),

            2,

        )


# ============================================================
# GLOBAL SERVICE INSTANCE
# ============================================================

segmentation_service = (
    SegmentationService()
)