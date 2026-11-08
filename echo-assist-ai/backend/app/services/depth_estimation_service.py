import logging
from pathlib import Path

import cv2
import numpy as np
import torch


logger = logging.getLogger(
    "echo_assist.depth_estimation"
)


class DepthEstimationService:

    def __init__(self):

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.model_type = "MiDaS_small"

        self.model = None
        self.transform = None

        self.ready = False
        self.error_message = None

        # Defer model initialization until image inference is requested.
        # Core APIs must not depend on a local model cache or outbound download.


    # ========================================================
    # MODEL LOADING
    # ========================================================

    def _load_model(self):

        print("Loading MiDaS depth model...")

        try:

            hub_dir = Path(
                torch.hub.get_dir()
            )

            local_repo = (
                hub_dir
                / "intel-isl_MiDaS_master"
            )


            # ------------------------------------------------
            # LOAD FROM LOCAL CACHE
            # ------------------------------------------------

            if local_repo.exists():

                logger.info(
                    "Loading MiDaS from local cache: %s",
                    local_repo,
                )

                print(
                    f"Using local MiDaS cache: "
                    f"{local_repo}"
                )


                self.model = torch.hub.load(

                    str(local_repo),

                    self.model_type,

                    source="local",

                    trust_repo=True,
                )


                transforms = torch.hub.load(

                    str(local_repo),

                    "transforms",

                    source="local",

                    trust_repo=True,
                )


            # ------------------------------------------------
            # FIRST-TIME REMOTE DOWNLOAD
            # ------------------------------------------------

            else:

                logger.info(
                    "Local MiDaS cache not found. "
                    "Trying remote download."
                )

                print(
                    "MiDaS cache not found. "
                    "Trying remote download..."
                )


                self.model = torch.hub.load(

                    "intel-isl/MiDaS",

                    self.model_type,

                    trust_repo=True,
                )


                transforms = torch.hub.load(

                    "intel-isl/MiDaS",

                    "transforms",

                    trust_repo=True,
                )


            # ------------------------------------------------
            # PREPARE MODEL
            # ------------------------------------------------

            self.model.to(
                self.device
            )

            self.model.eval()


            if self.model_type == "MiDaS_small":

                self.transform = (
                    transforms.small_transform
                )

            else:

                self.transform = (
                    transforms.dpt_transform
                )


            self.ready = True

            self.error_message = None


            print(
                f"MiDaS ready on {self.device}"
            )


            logger.info(
                "MiDaS depth estimation ready on %s",
                self.device,
            )


        except Exception as exc:

            self.ready = False

            self.model = None

            self.transform = None

            self.error_message = str(exc)


            logger.exception(
                "MiDaS loading failed. "
                "Depth estimation will be unavailable, "
                "but the backend will continue running."
            )


            print(
                "WARNING: MiDaS depth model could not "
                "be loaded."
            )

            print(
                "Depth estimation disabled. "
                "Other backend services will continue."
            )


    # ========================================================
    # SERVICE STATUS
    # ========================================================

    def is_ready(self):

        return self.ready


    # ========================================================
    # GENERATE DEPTH MAP
    # ========================================================

    def generate_depth_map(
        self,
        image_path,
    ):

        if not self.ready:

            self._load_model()

        if not self.ready:

            raise RuntimeError(
                "Depth estimation service is unavailable. "
                f"Reason: {self.error_message}"
            )


        image = cv2.imread(
            str(image_path)
        )


        if image is None:

            raise ValueError(
                "Unable to read image for "
                "depth estimation"
            )


        rgb = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2RGB,
        )


        input_batch = (

            self.transform(rgb)

            .to(self.device)
        )


        with torch.no_grad():

            prediction = self.model(
                input_batch
            )


            prediction = (

                torch.nn.functional.interpolate(

                    prediction.unsqueeze(1),

                    size=rgb.shape[:2],

                    mode="bicubic",

                    align_corners=False,

                )

                .squeeze()
            )


        return (

            prediction
            .cpu()
            .numpy()
        )


    # ========================================================
    # OBJECT DEPTH
    # ========================================================

    def get_object_depth(
        self,
        depth_map,
        bounding_box,
    ):

        if depth_map is None:

            return None


        height, width = depth_map.shape


        x1 = max(
            0,
            int(bounding_box["x1"]),
        )

        y1 = max(
            0,
            int(bounding_box["y1"]),
        )

        x2 = min(
            width,
            int(bounding_box["x2"]),
        )

        y2 = min(
            height,
            int(bounding_box["y2"]),
        )


        if x2 <= x1 or y2 <= y1:

            return None


        object_region = depth_map[
            y1:y2,
            x1:x2,
        ]


        if object_region.size == 0:

            return None


        valid_values = object_region[
            np.isfinite(object_region)
        ]


        if valid_values.size == 0:

            return None


        median_depth = float(
            np.median(valid_values)
        )


        return round(
            median_depth,
            4,
        )


# ============================================================
# GLOBAL SERVICE INSTANCE
# ============================================================

depth_estimation_service = (
    DepthEstimationService()
)
