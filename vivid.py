from v4l2 import V4L2_CID_USER_BASE
VIVID_CID_CUSTOM_BASE                       = V4L2_CID_USER_BASE | 0xf000
VIVID_CID_BUTTON                            = VIVID_CID_CUSTOM_BASE + 0
VIVID_CID_BOOLEAN                           = VIVID_CID_CUSTOM_BASE + 1
VIVID_CID_INTEGER                           = VIVID_CID_CUSTOM_BASE + 2
VIVID_CID_INTEGER64                         = VIVID_CID_CUSTOM_BASE + 3
VIVID_CID_MENU                              = VIVID_CID_CUSTOM_BASE + 4
VIVID_CID_STRING                            = VIVID_CID_CUSTOM_BASE + 5
VIVID_CID_BITMASK                           = VIVID_CID_CUSTOM_BASE + 6
VIVID_CID_INTMENU                           = VIVID_CID_CUSTOM_BASE + 7
VIVID_CID_U32_ARRAY                         = VIVID_CID_CUSTOM_BASE + 8
VIVID_CID_U16_MATRIX                        = VIVID_CID_CUSTOM_BASE + 9
VIVID_CID_U8_4D_ARRAY                       = VIVID_CID_CUSTOM_BASE + 10
VIVID_CID_VIVID_BASE                        = 0x00f00000 | 0xf000
VIVID_CID_VIVID_CLASS                       = 0x00f00000 | 1
VIVID_CID_TEST_PATTERN                      = VIVID_CID_VIVID_BASE + 0
VIVID_CID_OSD_TEXT_MODE                     = VIVID_CID_VIVID_BASE + 1
VIVID_CID_HOR_MOVEMENT                      = VIVID_CID_VIVID_BASE + 2
VIVID_CID_VERT_MOVEMENT                     = VIVID_CID_VIVID_BASE + 3
VIVID_CID_SHOW_BORDER                       = VIVID_CID_VIVID_BASE + 4
VIVID_CID_SHOW_SQUARE                       = VIVID_CID_VIVID_BASE + 5
VIVID_CID_INSERT_SAV                        = VIVID_CID_VIVID_BASE + 6
VIVID_CID_INSERT_EAV                        = VIVID_CID_VIVID_BASE + 7
VIVID_CID_VBI_CAP_INTERLACED                = VIVID_CID_VIVID_BASE + 8
VIVID_CID_HFLIP                             = VIVID_CID_VIVID_BASE + 20
VIVID_CID_VFLIP                             = VIVID_CID_VIVID_BASE + 21
VIVID_CID_STD_ASPECT_RATIO                  = VIVID_CID_VIVID_BASE + 22
VIVID_CID_DV_TIMINGS_ASPECT_RATIO           = VIVID_CID_VIVID_BASE + 23
VIVID_CID_TSTAMP_SRC                        = VIVID_CID_VIVID_BASE + 24
VIVID_CID_COLORSPACE                        = VIVID_CID_VIVID_BASE + 25
VIVID_CID_XFER_FUNC                         = VIVID_CID_VIVID_BASE + 26
VIVID_CID_YCBCR_ENC                         = VIVID_CID_VIVID_BASE + 27
VIVID_CID_QUANTIZATION                      = VIVID_CID_VIVID_BASE + 28
VIVID_CID_LIMITED_RGB_RANGE                 = VIVID_CID_VIVID_BASE + 29
VIVID_CID_ALPHA_MODE                        = VIVID_CID_VIVID_BASE + 30
VIVID_CID_HAS_CROP_CAP                      = VIVID_CID_VIVID_BASE + 31
VIVID_CID_HAS_COMPOSE_CAP                   = VIVID_CID_VIVID_BASE + 32
VIVID_CID_HAS_SCALER_CAP                    = VIVID_CID_VIVID_BASE + 33
VIVID_CID_HAS_CROP_OUT                      = VIVID_CID_VIVID_BASE + 34
VIVID_CID_HAS_COMPOSE_OUT                   = VIVID_CID_VIVID_BASE + 35
VIVID_CID_HAS_SCALER_OUT                    = VIVID_CID_VIVID_BASE + 36
VIVID_CID_LOOP_VIDEO                        = VIVID_CID_VIVID_BASE + 37
VIVID_CID_SEQ_WRAP                          = VIVID_CID_VIVID_BASE + 38
VIVID_CID_TIME_WRAP                         = VIVID_CID_VIVID_BASE + 39
VIVID_CID_MAX_EDID_BLOCKS                   = VIVID_CID_VIVID_BASE + 40
VIVID_CID_PERCENTAGE_FILL                   = VIVID_CID_VIVID_BASE + 41
VIVID_CID_REDUCED_FPS                       = VIVID_CID_VIVID_BASE + 42
VIVID_CID_STD_SIGNAL_MODE                   = VIVID_CID_VIVID_BASE + 60
VIVID_CID_STANDARD                          = VIVID_CID_VIVID_BASE + 61
VIVID_CID_DV_TIMINGS_SIGNAL_MODE            = VIVID_CID_VIVID_BASE + 62
VIVID_CID_DV_TIMINGS                        = VIVID_CID_VIVID_BASE + 63
VIVID_CID_PERC_DROPPED                      = VIVID_CID_VIVID_BASE + 64
VIVID_CID_DISCONNECT                        = VIVID_CID_VIVID_BASE + 65
VIVID_CID_DQBUF_ERROR                       = VIVID_CID_VIVID_BASE + 66
VIVID_CID_QUEUE_SETUP_ERROR                 = VIVID_CID_VIVID_BASE + 67
VIVID_CID_BUF_PREPARE_ERROR                 = VIVID_CID_VIVID_BASE + 68
VIVID_CID_START_STR_ERROR                   = VIVID_CID_VIVID_BASE + 69
VIVID_CID_QUEUE_ERROR                       = VIVID_CID_VIVID_BASE + 70
VIVID_CID_CLEAR_FB                          = VIVID_CID_VIVID_BASE + 71
VIVID_CID_RADIO_SEEK_MODE                   = VIVID_CID_VIVID_BASE + 90
VIVID_CID_RADIO_SEEK_PROG_LIM               = VIVID_CID_VIVID_BASE + 91
VIVID_CID_RADIO_RX_RDS_RBDS                 = VIVID_CID_VIVID_BASE + 92
VIVID_CID_RADIO_RX_RDS_BLOCKIO              = VIVID_CID_VIVID_BASE + 93
VIVID_CID_RADIO_TX_RDS_BLOCKIO              = VIVID_CID_VIVID_BASE + 94
VIVID_CID_SDR_CAP_FM_DEVIATION              = VIVID_CID_VIVID_BASE + 110
