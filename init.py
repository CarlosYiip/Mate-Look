#!/usr/bin/env python3.5

import sqlite3, os, glob, re

# Script for extracting user information from folders and store them in a data base named matelook.db

# Schema
conn = sqlite3.connect('matelook.db')

conn.execute("DROP TABLE userinfo;")

conn.execute("DROP TABLE relations;")

conn.execute("DROP TABLE enrollments;")

conn.execute("DROP TABLE posts;")

conn.execute("DROP TABLE comments;")

conn.execute("DROP TABLE replies;")

conn.execute("DROP TABLE mentioned_in_post;")

conn.execute("DROP TABLE mentioned_in_comment;")

conn.execute("DROP TABLE mentioned_in_reply;")

conn.execute("""
CREATE  TABLE   userinfo (
    user_id     INTEGER NOT NULL PRIMARY KEY,
    full_name   TEXT    NOT NULL,
    password    TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    birthday    TEXT,
    program     TEXT,
    home_suburb TEXT,
    home_lat    REAL,
    home_lon    REAL,
    profile     TEXT);
""")

conn.execute("""
CREATE  TABLE   relations (
    user_id     INTEGER,
    mate_id     INTEGER);
""")

conn.execute("""
CREATE TABLE    enrollments (
    user_id     INTEGER,
    course      TEXT);
""")

conn.execute("""
CREATE TABLE    posts (
    post_id     INTEGER NOT NULL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    post_time        TEXT    NOT NULL,
    content     TEXT);       
""")

conn.execute("""
CREATE TABLE    comments (
    comment_id  INTEGER NOT NULL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    post_id     INTEGER NOT NULL,
    comment_time        TEXT    NOT NULL,
    content     TEXT);
""")

conn.execute("""
CREATE TABLE    replies (
    reply_id    INTEGER NOT NULL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    comment_id  INTEGER NOT NULL,
    reply_time  TEXT    NOT NULL,
    content     TEXT);
""")

conn.execute("""
CREATE TABLE    mentioned_in_post (
    user_id     INTEGER NOT NULL,
    post_id     INTEGER NOT NULL,
    PRIMARY KEY (user_id, post_id));
""")

conn.execute("""
CREATE TABLE    mentioned_in_comment (
    user_id     INTEGER NOT NULL,
    comment_id     INTEGER NOT NULL,
    PRIMARY KEY (user_id, comment_id));
""")

conn.execute("""
CREATE TABLE    mentioned_in_reply (
    user_id     INTEGER NOT NULL,
    reply_id     INTEGER NOT NULL,
    PRIMARY KEY (user_id, reply_id));
""")


current_dir = os.getcwd()
# Use medium dataset
dataset_path = os.path.join(current_dir, "dataset-medium")
users = sorted(glob.glob(os.path.join(dataset_path, "*")))

post_id = 0
comment_id = 0
reply_id = 0

for u in users:
    user_filename = os.path.join(u, "user.txt")
    if not os.path.isfile(user_filename):
        continue
    with open(user_filename) as f:
        user_info = f.read()
    # Read all userinfo from user.txt
    match = re.search('zid=z(.+)\n', user_info)
    if match:
        user_id = match.group(1)
        
    match = re.search('password=(.+)\n', user_info)
    if match:
        user_password = match.group(1)
        
    match = re.search('full_name=(.+)\n', user_info)
    if match:
        user_full_name = match.group(1)

    match = re.search('birthday=(.+)\n', user_info)
    if match:
        user_birthday = match.group(1)

    match = re.search('email=(.+)\n', user_info)
    if match:
        user_email = match.group(1)

    match = re.search('program=(.+)\n', user_info)
    if match:
        user_program = match.group(1)

    match = re.search('home_suburb=(.+)\n', user_info)
    if match:
        user_home_suburb = match.group(1)
    else:
        user_home_suburb = None

    match = re.search('home_latitude=(.+)\n', user_info)
    if match:
        user_home_lat = float(match.group(1))
    else:
        user_home_lat = None
        
    match = re.search('home_longitude=(.+)\n', user_info)
    if match:
        user_home_lon = float(match.group(1))
    else:
        user_home_lon = None

    # Insert user personal information
    conn.execute("""
    INSERT INTO userinfo
    (user_id, full_name, password, email, birthday, program, home_suburb, home_lat, home_lon, profile)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (user_id, user_full_name, user_password, user_email, user_birthday,
          user_program, user_home_suburb, user_home_lat, user_home_lon, ""))

    # Get user's mate information
    match = re.search('mates=\[(.+)\]\n', user_info)
    if match:
        user_mate_list = match.group(1).split(', ')

    # Insert mate information
    for mate_id in user_mate_list:
        mate_id = re.sub('\D', '', mate_id)
        conn.execute("""
        INSERT INTO relations (user_id, mate_id)
        VALUES (?, ?);
        """, (user_id, mate_id))

    # Get user's enrollment information
    match = re.search('courses=\[(.+)\]\n', user_info)
    if match:
        user_course_list = match.group(1).split(', ')

    # Insert user's enrollment information
    for course in user_course_list:
        conn.execute("""
        INSERT INTO enrollments (user_id, course)
        VALUES (?, ?);
        """, (user_id, course))

    # Get all of the user's posts
    users_posts_path = os.path.join(u, "posts")
    posts_dir = sorted(glob.glob(os.path.join(users_posts_path, "*")))

    for post_path in posts_dir:
        post_file = os.path.join(post_path, 'post.txt')
        with open(post_file, 'r', encoding='utf-8') as f:
            post_info = f.read()
            
        match = re.search('message=(.+)\n', post_info, re.UNICODE)
        if match:
            post_content = match.group(1).encode(encoding='utf-8')

        match = re.search('time=(.+)\n', post_info)
        if match:
            post_time = match.group(1)

        match = re.search('from=z(.+)\n', post_info)
        if match:
            post_user_id = match.group(1)
            
        conn.execute("""
        INSERT INTO posts (post_id, user_id, post_time, content)
        VALUES (?, ?, ?, ?);
        """, (post_id, user_id, post_time, post_content))

        match = re.findall('z(\d+)', post_content.decode('utf-8', 'strict'))
        if match:
            for u_id in match:
                conn.execute("""
                INSERT INTO mentioned_in_post (user_id, post_id)
                VALUES (?, ?);
                """, (u_id, post_id))

        # Get all of the comments under this post
        comments_dir = os.path.join(post_path, 'comments')
        if os.path.isdir(comments_dir):
            for comment_path in sorted(glob.glob(os.path.join(comments_dir, "*"))):
                comment_file = os.path.join(comment_path, 'comment.txt')
                with open(comment_file, 'r', encoding='utf-8') as f:
                    comment_info = f.read()

                match = re.search('message=(.+)\n', comment_info)
                if match:
                    comment_content = match.group(1).encode(encoding='utf-8')

                match = re.search('from=z(.+)\n', comment_info)
                if match:
                    comment_user_id = match.group(1)

                match = re.search('time=(.+)\n', comment_info)
                if match:
                    comment_time = match.group(1)

                conn.execute("""
                INSERT INTO comments (comment_id, user_id, post_id, comment_time, content)
                VALUES (?, ?, ?, ?, ?);
                """, (comment_id, comment_user_id, post_id, comment_time, comment_content))

                match = re.findall('z(\d+)', comment_content.decode('utf-8', 'strict'))
                if match:
                    for u_id in match:
                        conn.execute("""
                        INSERT INTO mentioned_in_comment (user_id, comment_id)
                        VALUES (?, ?);
                        """, (u_id, comment_id))

                # Get all of the replies under this comment
                replies_dir = os.path.join(comment_path, 'replies')
                if os.path.isdir(replies_dir):
                    for reply_path in sorted(glob.glob(os.path.join(replies_dir, "*"))):
                        reply_file = os.path.join(reply_path, 'reply.txt')
                        with open(reply_file, 'r', encoding='utf-8') as f:
                            reply_info = f.read()

                        match = re.search('message=(.+)\n', reply_info)
                        if match:
                            reply_content = match.group(1).encode(encoding='utf-8')

                        match = re.search('from=z(.+)\n', reply_info)
                        if match:
                            reply_user_id = match.group(1)

                        match = re.search('time=(.+)\n', reply_info)
                        if match:
                            reply_time = match.group(1)
                            
                        conn.execute("""
                        INSERT INTO replies (reply_id, user_id, comment_id, reply_time, content)
                        VALUES (?, ?, ?, ?, ?);
                        """,(reply_id, reply_user_id, comment_id, reply_time, reply_content))
                        
                        match = re.findall('z(\d+)', reply_content.decode('utf-8', 'strict'))
                        if match:
                            for u_id in match:
                                conn.execute("""
                                INSERT INTO mentioned_in_reply (user_id, reply_id)
                                VALUES (?, ?);
                                """, (u_id, reply_id))
                        reply_id += 1
                comment_id += 1
        post_id += 1  
conn.commit()
conn.close()
