-- schema.sql

drop database if exists yulan_blog;

create database yulan_blog;

use yulan_blog;

create table users (
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `passwd` varchar(50) not null,
    `admin` bool not null,
    `name` varchar(50) not null,
    `created_at` real not null,
    unique key `idx_email` (`email`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table blogs (
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `name` varchar(50) not null,
    `summary` varchar(200) not null,
    `content` mediumtext not null,
    `content_html` mediumtext not null,
    `created_at` real not null,
    `revised_at` real not null,
    `page_view` bigint not null,
    `classfication` varchar(20) not null,
    primary key (`id`)
) engine=innodb default charset=utf8;

create table comments (
    `id` varchar(50) not null,
    `blog_id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `reply_to` varchar(50) not null,
    `parent_id` varchar(50) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    `blog_name` varchar(50) not null,
    primary key (`id`)
) engine=innodb default charset=utf8;