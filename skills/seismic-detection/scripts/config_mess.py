"""PALM MFT config template for seismic-detection skill.

Copy this file to your run directory as config_<CASE>.py, then adjust
the parameters marked [REGION-DEPENDENT] based on your data and user
confirmation. Values shown are Eryuan (Dali, Yunnan) defaults.

Parameters marked [FIXED] are method-level constants — do not change
unless the user explicitly requests it.
"""
import sys
from pathlib import Path

# Add PALM source to path (adjust ROOT to your PALM checkout location)
PALM_ROOT = Path(__file__).resolve().parent.parent / "knowledge/repos/PALM"
sys.path.insert(0, str(PALM_ROOT / "PAL_src"))
sys.path.insert(0, str(PALM_ROOT / "MFT_src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import data_pipeline as dp


class Config(object):
    def __init__(self):

        # =====================================================
        # [REGION-DEPENDENT] — MUST be confirmed with user per region
        # =====================================================

        self.freq_band = [1., 20.]       # analysis band; depends on archive
                                         # preprocessing and noise levels
        self.max_sta = 20                # max stations per template;
                                         # depends on network density
        self.min_sta = 4                 # min stations; too low → noise
        self.trig_thres = 0.3            # per-channel trigger; scan at 0.3,
                                         # deliver tiers at user-specified CC

        # =====================================================
        # [FIXED] — method constants, do not change without user request
        # =====================================================

        self.min_snr = 0                 # full-catalog templates, no gate
        self.win_snr = [1, 1]
        self.win_sta_lta = [8, 1]
        self.template_preprocess_padding_sec = 15.0
        self.template_shard_size = 512
        self.template_log_interval = 10
        self.temp_win_det = [1., 9.]    # P-1 to P+9 (PALM paper default)
        self.temp_win_p = [0.5, 1.5]
        self.temp_win_s = [0.5, 2.5]
        self.expand_len = 1.
        self.det_gap = 5.
        self.pick_win_p = [1.0, 1.0]
        self.pick_win_s = [1.6, 1.6]
        self.chn_p = [2]
        self.chn_s = [0, 1]
        self.amp_win = [1, 5]

        # =====================================================
        # [FIXED] association and hypoDD — established by Eryuan run
        # =====================================================

        self.association_origin_time_tolerance_sec = 2.0
        self.association_detection_cc_min = 0.3
        self.association_phase_cc_min = 0.4
        self.association_max_phase_shift_sec = [0.6, 1.0]
        self.association_min_neighbor_templates = 2
        self.association_max_neighbor_templates = 30
        self.association_start_event_id = 1000000
        self.hypodd_depth_offset_km = 0.0  # MUST be 0; see SKILL.md pitfall #7

        # =====================================================
        # [FIXED] processing — tied to archive schema
        # =====================================================

        self.data_buffer_sec = 30.0
        self.taper_max_length_sec = 5.0
        self.samp_rate = 50
        self.phase_samp_rate = 100
        self.num_workers = 10
        self.get_data_dict = dp.get_data_dict
        self.channel_priority = ["HH", "BH", "EH", "HN", "EN", "SH"]
        self.location_priority = ["10", "20", "01", "02", "00", ""]
        self.station_selection_order = "channel_first"
        self.get_sta_dict = dp.get_sta_dict
