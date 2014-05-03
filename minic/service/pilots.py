# -*- coding: utf-8 -*-
"""
Commander's pilots service.
"""
import tx_logging

from il2ds_middleware.service import MutedPilotsService
from minic.service import ClientServiceMixin


LOG = tx_logging.getLogger(__name__)


class PilotsService(MutedPilotsService, ClientServiceMixin):
    """
    Custom service for managing online pilots.
    """
