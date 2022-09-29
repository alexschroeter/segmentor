from stardist.models import StarDist3D
from csbdeep.utils import Path, normalize
import sys
import numpy as np
import xarray as xr
from concurrent.futures import ThreadPoolExecutor
import asyncio
from arkitekt.apps.connected import ConnectedApp
from fakts.grants.remote.device_code import DeviceCodeGrant
from fakts.grants.remote.base import StaticDiscovery
from fakts import Fakts
from mikro.api.schema import RepresentationFragment, from_xarray, RepresentationVariety
from rekuest.actors.functional import (
    CompletlyThreadedActor,
)
from pydantic import Field

model = StarDist3D(None, name="stardist3", basedir="models")

app = ConnectedApp(
    fakts=Fakts(
        subapp="stardist",
        grant=DeviceCodeGrant(
            open_browser=False,
            name="stardist",
            discovery=StaticDiscovery(base_url="http://herre:8000/f/"),
        ),
    )
)


@app.rekuest.register(gpu=True)
class segment_cells(CompletlyThreadedActor):
    executor: ThreadPoolExecutor = Field(
        default_factory=lambda: ThreadPoolExecutor(max_workers=1)
    )
    _model: StarDist3D

    def provide(self, provision):
        self._model = StarDist3D(None, name="stardist2", basedir="models")
        return None

    def assign(self, rep: RepresentationFragment) -> RepresentationFragment:
        """Segment Cells

        Segments Cells using the stardist algorithm

        Args:
            rep (Representation): The Representation.

        Returns:
            Representation: A Representation

        """
        print(f"Called wtih Rep {rep.data.nbytes}")
        assert (
            rep.data.nbytes < 1000 * 1000 * 30 * 1 * 2
        ), "Image is to big to be loaded"

        axis_norm = (0, 1, 2)
        x = rep.data.sel(c=0, t=0).transpose(*"zxy").data.compute()
        x = normalize(x, 1, 99.8, axis=axis_norm)

        labels, details = model.predict_instances(x)

        array = xr.DataArray(labels, dims=list("zxy"))

        nana = from_xarray(
            array,
            name="Segmented " + rep.name,
            origins=[rep],
            tags=["segmented"],
            variety=RepresentationVariety.MASK,
        )
        return nana

    def unprovide(self):
        return None


with app:
    app.rekuest.run()