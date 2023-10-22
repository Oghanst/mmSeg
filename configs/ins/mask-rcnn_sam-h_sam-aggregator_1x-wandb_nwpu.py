max_epochs = 300

# ----- mask-rcnn_r50_fpn.py ------
# model settings

# backbone
custom_imports = dict(imports=['mmpretrain.models'], allow_failed_imports=False)
# pretrained = '/nfs/home/3002_hehui/xmx/pretrain/sam/sam_vit_h_4b8939.pth'
pretrained ='https://download.openmmlab.com/mmclassification/v1/vit_sam/vit-huge-p16_sam-pre_3rdparty_sa1b-1024px_20230411-3f13c653.pth'
# model = dict(
#     type='ImageClassifier',
#     backbone=dict(
#         type='ViTSAM',
#         arch='huge',
#         img_size=1024,
#         patch_size=16,
#         out_channels=256,
#         use_abs_pos=True,
#         use_rel_pos=True,
#         window_size=14,
#     ),
#     neck=None,
#     head=None,
# )

from rsseg.models import SAMAggregatorNeck

model = dict(
    type='mmdet.MaskRCNN',
    data_preprocessor=dict(
        type='mmdet.DetDataPreprocessor',
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        bgr_to_rgb=True,
        pad_mask=True,
        pad_size_divisor=32),
    backbone=dict(
        type='mmpretrain.ViTSAM',
        arch='huge',
        img_size=1024,
        patch_size=16,
        out_channels=256,
        use_abs_pos=True,
        use_rel_pos=True,
        window_size=14,
        # num_stages=2,
        # out_indices=(0, 1, 2, 3),
        # out_indices=(0,1),
        init_cfg=dict(
            type='Pretrained',
            checkpoint=pretrained,
            prefix='backbone.',
        )
    ),
    # neck=dict(
    #     type='FPN',
    #     # in_channels=[256, 512, 1024, 2048],
    #     in_channels=[256, 256, 256, 256],
    #     out_channels=256,
    #     num_outs=5),
    neck=dict(
        type=SAMAggregatorNeck,
        in_channels=[1280] * 32,
        # in_channels=[768] * 12,
        inner_channels=256,
        # selected_channels=range(1, 32, 2),
        selected_channels=range(32),
        # selected_channels=range(4, 12, 2),
        out_channels=256,
        up_sample_scale=4,
    ),
    rpn_head=dict(
        type='mmdet.RPNHead',
        in_channels=256,
        feat_channels=256,
        anchor_generator=dict(
            type='mmdet.AnchorGenerator',
            scales=[8],
            ratios=[0.5, 1.0, 2.0],
            strides=[4, 8, 16, 32, 64]),
        bbox_coder=dict(
            type='mmdet.DeltaXYWHBBoxCoder',
            target_means=[.0, .0, .0, .0],
            target_stds=[1.0, 1.0, 1.0, 1.0]),
        loss_cls=dict(
            type='mmdet.CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0),
        loss_bbox=dict(type='mmdet.L1Loss', loss_weight=1.0)),
    roi_head=dict(
        type='mmdet.StandardRoIHead',
        bbox_roi_extractor=dict(
            type='mmdet.SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=7, sampling_ratio=0),
            out_channels=256,
            featmap_strides=[4, 8, 16, 32]),
        bbox_head=dict(
            type='mmdet.Shared2FCBBoxHead',
            in_channels=256,
            fc_out_channels=1024,
            roi_feat_size=7,
            num_classes=80,
            bbox_coder=dict(
                type='mmdet.DeltaXYWHBBoxCoder',
                target_means=[0., 0., 0., 0.],
                target_stds=[0.1, 0.1, 0.2, 0.2]),
            reg_class_agnostic=False,
            loss_cls=dict(
                type='mmdet.CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0),
            loss_bbox=dict(type='L1Loss', loss_weight=1.0)),
        mask_roi_extractor=dict(
            type='mmdet.SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=14, sampling_ratio=0),
            out_channels=256,
            featmap_strides=[4, 8, 16, 32]),
        mask_head=dict(
            type='mmdet.FCNMaskHead',
            num_convs=4,
            in_channels=256,
            conv_out_channels=256,
            num_classes=80,
            loss_mask=dict(
                type='mmdet.CrossEntropyLoss', use_mask=True, loss_weight=1.0))),
    # model training and testing settings
    train_cfg=dict(
        rpn=dict(
            assigner=dict(
                type='mmdet.MaxIoUAssigner',
                pos_iou_thr=0.7,
                neg_iou_thr=0.3,
                min_pos_iou=0.3,
                match_low_quality=True,
                ignore_iof_thr=-1),
            sampler=dict(
                type='mmdet.RandomSampler',
                num=256,
                pos_fraction=0.5,
                neg_pos_ub=-1,
                add_gt_as_proposals=False),
            allowed_border=-1,
            pos_weight=-1,
            debug=False),
        rpn_proposal=dict(
            nms_pre=2000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            assigner=dict(
                type='mmdet.MaxIoUAssigner',
                pos_iou_thr=0.5,
                neg_iou_thr=0.5,
                min_pos_iou=0.5,
                match_low_quality=True,
                ignore_iof_thr=-1),
            sampler=dict(
                type='mmdet.RandomSampler',
                num=512,
                pos_fraction=0.25,
                neg_pos_ub=-1,
                add_gt_as_proposals=True),
            mask_size=28,
            pos_weight=-1,
            debug=False)),
    test_cfg=dict(
        rpn=dict(
            nms_pre=1000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            score_thr=0.05,
            nms=dict(type='nms', iou_threshold=0.5),
            max_per_img=100,
            mask_thr_binary=0.5)))


# ----- coco_instance.py -----
# dataset settings
# data_root = '/nfs/home/3002_hehui/xmx/COCO2017/'
backend_args = None

train_pipeline = [
    dict(type='LoadImageFromFile', backend_args=backend_args),
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(type='Resize', scale=(1333, 800), keep_ratio=True),
    dict(type='RandomFlip', prob=0.5),
    dict(type='PackDetInputs')
]
test_pipeline = [
    dict(type='LoadImageFromFile', backend_args=backend_args),
    dict(type='Resize', scale=(1333, 800), keep_ratio=True),
    # If you don't have a gt annotation, delete the pipeline
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(
        type='PackDetInputs',
        meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape',
                   'scale_factor'))
]

from mmdet.datasets import NWPUInsSegDataset
dataset_type = NWPUInsSegDataset
data_root = '/nfs/home/3002_hehui/xmx/data/NWPU/NWPU VHR-10 dataset'

train_dataloader = dict(
    batch_size=2,
    num_workers=2,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    batch_sampler=dict(type='AspectRatioBatchSampler'),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file='/nfs/home/3002_hehui/xmx/RS-SA/RSPrompter/data/NWPU/annotations/NWPU_instances_train.json',
        data_prefix=dict(img='positive image set'),
        filter_cfg=dict(filter_empty_gt=True, min_size=32),
        pipeline=train_pipeline,
        backend_args=backend_args))


val_dataloader = dict(
    batch_size=1,
    num_workers=2,
    persistent_workers=True,
    drop_last=False,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file='/nfs/home/3002_hehui/xmx/data/NWPU/NWPU VHR-10 dataset/nwpu-instances_val.json',
        data_prefix=dict(img='positive image set'),
        filter_cfg=dict(filter_empty_gt=True, min_size=32),
        test_mode=True,
        pipeline=test_pipeline,
        backend_args=backend_args)
)


test_dataloader = val_dataloader
from mmdet.evaluation.metrics import CocoMetric
val_evaluator = dict(
    type=CocoMetric,
    # ann_file=data_root + '/annotations/instances_val2017.json',
    ann_file='/nfs/home/3002_hehui/xmx/data/NWPU/NWPU VHR-10 dataset/nwpu-instances_val.json',
    metric=['bbox', 'segm'],
    format_only=False,
    backend_args=backend_args)
test_evaluator = val_evaluator

# ----- schedule_1x.py -----
# training schedule for 1x
train_cfg = dict(type='EpochBasedTrainLoop', max_epochs=max_epochs, val_interval=2)
val_cfg = dict(type='ValLoop')
test_cfg = dict(type='TestLoop')

# learning rate
param_scheduler = [
    dict(
        type='LinearLR', start_factor=0.001, by_epoch=False, begin=0, end=500),
    dict(
        type='MultiStepLR',
        begin=0,
        end=12,
        by_epoch=True,
        milestones=[8, 11],
        gamma=0.1)
]

# optimizer
optim_wrapper = dict(
    type='OptimWrapper',
    # optimizer=dict(type='SGD', lr=0.02, momentum=0.9, weight_decay=0.0001)
    optimizer=dict(type='Adam', lr=0.0005, weight_decay=0.0001)
)

# Default setting for scaling LR automatically
#   - `enable` means enable scaling LR automatically
#       or not by default.
#   - `base_batch_size` = (8 GPUs) x (2 samples per GPU).
auto_scale_lr = dict(enable=False, base_batch_size=16)



# ----- default_runtime -----
default_scope = 'mmdet'

default_hooks = dict(
    timer=dict(type='IterTimerHook'),
    logger=dict(type='LoggerHook', interval=50),
    param_scheduler=dict(type='ParamSchedulerHook'),
    checkpoint=dict(type='CheckpointHook', interval=4),
    sampler_seed=dict(type='DistSamplerSeedHook'),
    visualization=dict(type='DetVisualizationHook'))

env_cfg = dict(
    cudnn_benchmark=False,
    mp_cfg=dict(mp_start_method='fork', opencv_num_threads=0),
    dist_cfg=dict(backend='nccl'),
)

# vis_backends = [dict(type='LocalVisBackend')]
# vis_backends = [dict(type='LocalVisBackend'), dict(type='WandbVisBackend')]
vis_backends = [dict(type='LocalVisBackend'), dict(type='WandbVisBackend',init_kwargs=dict(project='dev',name='mask-rcnn_sam-h_fpn-nwpu'))]
visualizer = dict(
    type='mmdet.DetLocalVisualizer', vis_backends=vis_backends, name='visualizer')
log_processor = dict(type='LogProcessor', window_size=50, by_epoch=True)

log_level = 'INFO'
load_from = None
resume = False


# ------------- ------------
# vis_backends = [dict(type='LocalVisBackend'), dict(type='WandbVisBackend')]
# visualizer = dict(vis_backends=vis_backends)

# MMEngine support the following two ways, users can choose
# according to convenience
# default_hooks = dict(checkpoint=dict(interval=4))
# _base_.default_hooks.checkpoint.interval = 4

# train_cfg = dict(val_interval=2)
# _base_.train_cfg.val_interval = 2

find_unused_parameters = True