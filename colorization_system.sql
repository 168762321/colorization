/*
Navicat MySQL Data Transfer
Date: 2021-12-01 10:15:45
*/

-- ----------------------------
-- Table structure for project
-- ----------------------------

DROP TABLE IF EXISTS `project`;

CREATE TABLE `project` (
    `id` smallint(6) NOT NULL AUTO_INCREMENT,
    `name` varchar(255) NOT NULL COMMENT '项目名称',
    `project_path` varchar(255) DEFAULT NULL COMMENT '项目路径',
    `video_path` varchar(255) DEFAULT NULL COMMENT '源视频路径',
    `video_fps` smallint(3) DEFAULT 25 COMMENT '源视频帧率',
    `frame_suffix` varchar(6) DEFAULT 'png' COMMENT '源视频帧图像后缀',
    `frame_path` varchar(255) DEFAULT NULL COMMENT '源视频帧图像路径',
    `frame_min_index` smallint(6) zerofill DEFAULT NULL COMMENT '源视频帧图像最小索引',
    `frame_max_index` smallint(6) zerofill DEFAULT NULL COMMENT '源视频帧图像最大索引',
    `create_time` datetime NOT NULL DEFAULT current_timestamp() COMMENT '创建时间',
    `update_time` datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `name_idx` (`name`) USING BTREE,
    KEY `id` (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for shortcut
-- ----------------------------
DROP TABLE IF EXISTS `shortcut`;

CREATE TABLE `shortcut` (
	`id` smallint(6) NOT NULL AUTO_INCREMENT,
    `name` varchar(255) NOT NULL COMMENT '片段名称',
    `project_id` smallint(6) NOT NULL COMMENT '所属项目id',
    `colorizer_id`  smallint(6) COMMENT '最终上色版本id',
    `frame_min_index` smallint(6) zerofill NOT NULL COMMENT '片段帧最小索引',
    `frame_max_index` smallint(6) zerofill NOT NULL COMMENT '片段帧最大索引',
    `colloidal` tinyint(1) DEFAULT 0 COMMENT '是否胶质(0:否 1:是)',
    `noise_level` tinyint(1) DEFAULT 0 COMMENT '噪音等级(0 1 2 3 4 5)',
    `refer_frame_indexs` smallint(6) zerofill DEFAULT NULL COMMENT '参考帧索引, <,>分割',
    `colorize_state` tinyint(1) DEFAULT 0 COMMENT '是否完成上色(0:否 1:是)',
    `create_time` datetime NOT NULL DEFAULT current_timestamp() COMMENT '创建时间',
    `update_time` datetime DEFAULT NULL COMMENT '更新时间',
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for colorizer
-- ----------------------------
DROP TABLE IF EXISTS `colorizer`;

CREATE TABLE `colorizer` (
	`id` smallint(6) NOT NULL AUTO_INCREMENT,
    `shortcut_id` smallint(6) NOT NULL COMMENT '所属片段id',
    `colorize_refer_frame_path` varchar(255) NOT NULL COMMENT '上传彩色参考帧路径',
    `output_path` varchar(255) NOT NULL COMMENT '上色输出路径',
    `colorize_state` tinyint(1) DEFAULT 0 COMMENT '是否完成上色(0:否 1:是)',
    `create_time` datetime NOT NULL DEFAULT current_timestamp() COMMENT '创建时间',
    `update_time` datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
