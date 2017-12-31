#!/usr/bin/env python3.5
import cgi, cgitb, os, re, sqlite3, sys, codecs, datetime, smtplib, collections

global users_dir
users_dir = "dataset-medium"

global parameters
parameters = cgi.FieldStorage() 


def main():
    print(page_header())
    cgitb.enable()
    keys = parameters.keys()
    if 'login' in keys:
        # Insert record into database after user have made a new post, comment or reply
        if 'new_post_content' in keys:
            insert_new_message('post')
        elif 'new_comment_content' in keys:
            insert_new_message('comment')
        elif 'new_reply_content' in keys:
            insert_new_message('reply')

        # Insert or delete relations (follow or unfollow mates) from database
        if 'follow_mate_id' in keys:
            insert_new_relation()
        elif 'unfollow_mate_id' in keys:
            delete_existed_relation()

        # Update user profile
        if "update_profile" in keys:
            insert_new_profile()

        # Update user information
        if 'EDIT_info' in keys:
            edit_information()

        # Upload user profile image
        if 'upload_image' in keys:
            update_user_image()

        # Delete message
        if 'delete_post_id' in keys or 'delete_comment_id' in keys or 'delete_reply_id' in keys:
            delete_message()

        # Go to the mates page which shows all of the user's friend
        if 'mates' in keys:
            print(mates_page(parameters.getvalue("user_id")))
        # Go to the mates' mates page which shows all of user's mate's mates
        elif 'matemates' in keys:
            print(mates_page(parameters.getvalue("page_user_id")))
        # Go to the search user page
        elif 'search_name' in keys:
            print(search_user_page())
        # Go to the search post page:
        elif 'search_post' in keys:
            print(search_post_page())
        # Go to the page that shows all user search result
        elif 'requested_user_name' in keys:
            print(matching_user_page())
        # Go to the page that shows all matching posts:
        elif 'requested_post' in keys:
            print(matching_post_page())
        # Go to user personal page (Mate's or logged in users)
        elif 'page_user_id' in keys:
            print(user_page())
        # Go to the home page that shows all latest post
        elif 'home_page' in keys:
            # If just made a new post, insert the record into database
            print(home_page())
        # Go to mates suggestion page
        elif 'mate_suggestion' in keys:
            print(mate_suggestion_page())
        elif 'edit_information' in keys:
            print(edit_information_page())
    # Go back to login page if user just logged out
    elif 'logout' in keys:
        print(login_page())
    # Go to login page and validate user input username and password
    elif 'validation' in keys:
        print(validation())
    # Go to account creation page to fill in personal information
    elif 'account_creation' in keys:
        print(account_creation_page())
    # Check the information submitted by new user
    # If all information are valid, system will send an verification email to user
    elif 'check_account_creation' in keys:
        print(check_account_creation())
    # After user click the link included in the verification email, the process of account creation
    # is completed and user would be redirected to his/her home page
    elif 'insert_new_account' in keys:
        print(insert_new_account())
    # Go to password recovery page to input user email
    elif 'password_recovery' in keys:
        print(password_recovery_page())
    # Verify user input email
    elif 'recover_email' in keys:
        print(recover_check_page())
    # Prompt user to set an new email
    elif 'set_new_password' in keys:
        print(set_new_password_page())
    # Update the record in database and redirect user to login page
    elif 'new_password' in keys:
        print(set_new_password())
    else:
        print(login_page())
    print(page_trailer())


def login_page():
    # Generate html code for login page
    html = '<div class="matelook_input">\n'
    html += '<form>\n'
    html += 'User Id:<br>\n'
    # Get user input id
    html += '<input type="text" name="user_id"><br>\n'
    html += '<p>\n'
    html += 'Password:<br>\n'
    # Get user input password
    html += '<input type="password" name="password">\n'
    html += '<p>\n'
    html += '<input type="submit" name="validation" value="Login">\n'
    html += '<input type="submit" name="account_creation" value="Create account">\n'
    html += '<input type="submit" name="password_recovery" value="Forget your password?">\n'
    html += '</form>\n'
    html += '</div>\n'
    return html


def account_creation_page():
    # Generate html code for user to fill his/her account information
    html = '<div class="matelook_input">\n'
    html += '<h2> Create Account </h2>\n'
    html += '<form>\n'
    html += 'Z id: <input type="text" placeholder="z1234567" name="create_z_id">\n<p>\n'
    html += 'Password: <input type="password" name="create_password">\n<p>\n'
    html += 'Full Name: <input type="text" name="create_full_name">\n<p>\n'
    html += 'Email: <input type="text" name="create_email">\n<p>\n'
    html += 'Program: <input type="text" name="create_program">\n<p>\n'
    html += 'Suburb: <input type="text" name="create_suburb">\n<p>\n'
    html += 'Birthday: <input type="date" name="create_birthday" placeholder="YYYY-MM-DD">\n<p>\n'
    html += 'Home latitude: <input type="text" name="create_home_long">\n<p>\n'
    html += 'Home Longitude: <input type="text" name="create_home_lat">\n<p>\n'
    html += '<input type="submit" value="Create Account" name="check_account_creation">\n'
    html += '<input type="submit" value="Cancel" name="check_account_creation">\n'
    html += '</form>\n'
    html += '</div>'
    return html


def check_account_creation():
    html = ''
    warning_message = ''

    # If not all the fields have been filled, user would receive a warning message
    # and be redirected back to the account creation page
    if len(parameters.keys()) != 10:
        recreate_html = '<h2> All Fields should be filled </h2>\n'
        recreate_html += account_creation_page()
        return recreate_html

    # Check user input Z id is valid or not
    # 1. Must be in the pattern of ([Zz]\d{7})
    z_id = str(parameters.getvalue("create_z_id"))
    match = re.fullmatch("^[zZ](\d{7})$", z_id)
    valid_z_id = True
    if not match:
        warning_message += 'Z id must be in the pattern of z1234567<br>\n'
        valid_z_id = False
    # 2. This Z id must not been registered
    else:
        z_id = match.group(1)
        c.execute("SELECT * FROM userinfo WHERE user_id = {}".format(z_id))
        result = c.fetchone()
        if result:
            warning_message += 'This z id has been registered<br>\n'
            valid_z_id = False

    # Check user input email valid or not
    email = str(parameters.getvalue('create_email'))
    # 1. Patten check
    match = re.fullmatch("^\w+\@\w+(\.[A-Za-z]+)+$", email)
    valid_email = True
    if not match:
        warning_message += 'Incorrect email format<br>\n'
        valid_email = False
    # 2. This email must not been registered
    else:
        email = match.group(0)
        c.execute("SELECT * FROM userinfo WHERE email = '{}';".format(email))
        result = c.fetchone()
        if result:
            warning_message += "This email has already been registered<br>\n"
            valid_email = False

    # Check user input birthday format
    birthday = str(parameters.getvalue("create_birthday"))
    match = re.fullmatch("^\d\d\d\d-\d\d-\d\d$", birthday)
    valid_birthday = True
    if not match:
        valid_birthday = False
        warning_message += 'Incorrect birthday format'

    # If not all in correct format, redirect user to account creation page and print a warning message
    if not valid_email or not valid_z_id or not valid_birthday:
        recreate_html = '<h2> {} </h2>\n'.format(warning_message)
        recreate_html += account_creation_page()
        return recreate_html

    # All information provided by user are valid
    password = parameters.getvalue("create_password")
    full_name, program = parameters.getvalue("create_full_name"), parameters.getvalue("create_program")
    suburb = parameters.getvalue("create_suburb")
    home_lat, home_long = parameters.getvalue("create_home_lat"), parameters.getvalue("create_home_long")

    # User a dictionary to store all the information
    new_user_info = dict()
    new_user_info["z_id"] = z_id
    new_user_info["password"] = password
    new_user_info["full_name"] = full_name
    new_user_info["email"] = email
    new_user_info["program"] = program
    new_user_info["suburb"] = suburb
    new_user_info["birthday"] = birthday
    new_user_info["home_lat"] = home_lat
    new_user_info["home_long"] = home_long

    # Send a link to new user email and all the register information as parameters
    link = "http://127.0.0.1:2041/matelook.cgi?insert_new_account=1&"
    for arg_name in new_user_info:
        link += "&{}={}".format(arg_name, new_user_info[arg_name])
    link = re.sub("\s+", "%20", link)

    # Send users register information to his/her email in order to proceed
    # the account creation process
    send_email_verification(email, link)

    # Print notice and prompt user to check email
    html += '<h2>Verification email has been sent to your email</h2>\n'
    html += '<div class="matelook_input">\n'
    html += '<form>\n'
    html += '<input type="submit" value="Ok">\n'
    html += '</form>\n'
    html += '</div>\n'
    return html


def password_recovery_page():
    html = '<div class="matelook_input">\n'
    html += '<form>\n'
    html += '<h2> Please input your registered email </h2>\n'
    html += '<input type="text" name="recover_email">\n'
    html += '<input type="submit">\n'
    html += '</form>\n'
    return html


def recover_check_page():
    recover_email = parameters.getvalue("recover_email")
    # Check whether this email has benn registered
    c.execute("SELECT user_id FROM userinfo WHERE email = '{}'".format(recover_email))
    result = c.fetchone()

    html = '<div class="matelook_input">\n'
    # If not registered
    if not result:
        html += "<h2> No match record of your email </h2>"
        html += "<form\n>"
        html += '<input type="submit" value="Ok">\n'
        html += '</form>\n'
    # Send a link to this email
    else:
        user_id = result[0]
        html += "<h2> A password recovery email has been sent to you </h2>"
        html += "<form\n>"
        html += '<input type="submit" value="Ok">\n'
        html += '</form>\n'
        link = "http://127.0.0.1:2041/matelook.cgi?set_new_password=1&user_id={}".format(user_id)
        send_email_verification(recover_email, link)
    html += '</div>\n'
    return html


def set_new_password_page():
    # Prompt user to set a new password
    html = '<div class="matelook_input">\n'
    html += 'Set your new password<p>\n'
    html += '<form>\n'
    html += '<input type="password" name="new_password">\n'
    html += '<input type="hidden" name="user_id" value={}>\n'.format(parameters.getvalue("user_id"))
    html += '<p>\n<input type="submit">\n'
    html += '</form>\n'
    html += '</div>'
    return html


def set_new_password():
    # Update password for the user
    user_id = parameters.getvalue("user_id")
    new_password = parameters.getvalue("new_password")
    c.execute("UPDATE userinfo SET password = '{}' WHERE user_id = {}".format(new_password, user_id))
    conn.commit()
    redirectURL = 'matelook.cgi'.format(user_id)
    html = '<meta http-equiv="refresh" content="0;url=%s" />' % redirectURL
    return html


def send_email_verification(to, link):
    # Send email
    gmail_user = 'yezihaocarlos@gmail.com'
    gmail_pwd = 'carlos47594888'
    smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.login(gmail_user, gmail_pwd)
    header = 'To:' + to + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:Email Verification\n\n'
    msg = header + '\n\n Please click {} to finish your registration \n'.format(link)
    smtpserver.sendmail(gmail_user, to, msg)
    smtpserver.close()


def insert_new_account():
    # Get all user information from paramters
    z_id = int(parameters.getvalue("z_id"))
    password = str(parameters.getvalue("password"))
    full_name = str(parameters.getvalue("full_name"))
    email = str(parameters.getvalue("email"))
    program = str(parameters.getvalue("program"))
    suburb = str(parameters.getvalue("suburb"))
    birthday = str(parameters.getvalue("birthday"))
    home_lat = float(parameters.getvalue("home_lat"))
    home_long = float(parameters.getvalue("home_long"))

    # Insert user information into database
    c.execute("""INSERT INTO userinfo
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (z_id, full_name, password, email, birthday, program, suburb, home_lat, home_long, ''))
    conn.commit()

    # Redirect user to his/her home page
    redirectURL = 'matelook.cgi?user_id={}&login=1&home_page=1'.format(z_id)
    html = '<meta http-equiv="refresh" content="0;url=%s" />' % redirectURL
    return html


def validation():
    # Get user input from parameters
    user_input_user_id = parameters.getvalue('user_id')
    user_input_password = parameters.getvalue('password')

    # Get correct password from database by using user input id
    c.execute('SELECT password FROM userinfo WHERE user_id = ?', (user_input_user_id,))
    result = c.fetchone()
    # If no matching record, return an incorrect password or user id warning
    if not result:
        html = '<div class="matelook_warning">'
        html += '<h2> Incorrect username or password </h2>\n'
        html += '</div>\n'
        html += login_page()
        return html
    # Matching record exists
    else:
        # If user input password match correct password, direct user to his/her home page
        if result[0] == user_input_password:
            redirectURL = 'matelook.cgi?user_id={}&login=1&home_page=1'.format(user_input_user_id)
            html = '<meta http-equiv="refresh" content="0;url=%s" />' % redirectURL
            return html
        # Otherwise refresh login page with an incorrect password or user id warning
        else:
            html = '<div class="matelook_warning">'
            html += '<h2> Incorrect username or password </h2>\n'
            html += '</div>\n'
            html += login_page()
            return html


def insert_new_profile():
    new_profile = parameters.getvalue("new_profile_text")
    user_id = parameters.getvalue("user_id")
    # Insert new profile text into database
    c.execute("""UPDATE userinfo SET profile = '{}' WHERE user_id = '{}'""".format(new_profile, user_id))


def home_page():
    # Generate home page html

    user_id = parameters.getvalue('user_id')

    # Get html code for navigation bar
    html = navigation_bar()

    # Get user image path
    image_path = user_image_path(user_id)
    html += '<img src="{}" class="matelook_user_photo">\n'.format(image_path)

    # Get html code for user details
    user_info_html = user_info(user_id)
    html += user_info_html

    # Get html code for user posts
    make_post_html = make_post()
    html += make_post_html

    # Get the list of logged in users' mates from database
    c.execute('SELECT mate_id FROM relations WHERE user_id = ?', (user_id, ))
    mates_id = [i[0] for i in c.fetchall()]
    # Add the logged in user's id into this list
    mates_id.append(user_id)

    # Make a new list to store all posts to be shown
    latest_posts = []

    # Iterate through all the user id to get their posts and store them in latest_post list
    for m_id in mates_id:
        c.execute('SELECT * FROM posts WHERE user_id = ?', (m_id,))
        latest_posts += c.fetchall()

    # Sort the latest_post list by the order of post time
    latest_posts = sorted(latest_posts, key=lambda time: time[2], reverse=True)

    # Only show the three latest posts
    html += pagination(latest_posts, 'post')
    return html


def user_page():
    # Show logged in user main page or user's mate's page
    page_user_id = parameters.getvalue('page_user_id')

    # Get user info html
    user_info_html = user_info(page_user_id)

    # Get user image path, use No_Image_Available.jpg if there is no profile.jpg
    image_path = user_image_path(page_user_id)

    # Html for all user posts, including Date, time and post content
    posts_html = user_posts(page_user_id)

    # Cat all html code
    html = navigation_bar()
    html += '<img src="{}" class="matelook_user_photo">\n'.format(image_path)
    html += user_info_html

    # Update own profile
    if page_user_id == parameters.getvalue("user_id"):
        html += update_profile()

    # Follow and unfollow section
    page_user_id = parameters.getvalue("page_user_id")
    user_id = parameters.getvalue("user_id")

    # Only show follow or unfollow button when user is looking other user's page
    if page_user_id != user_id:
        html += follow_unfollow(page_user_id, user_id)
    html += posts_html
    return html


def mates_page(user_id):
    # Generate code of logged in user's mates list page

    # Get the list of the logged in user's mates who are being followed by user
    c.execute('SELECT mate_id FROM relations WHERE user_id = ?', (user_id, ))
    mates_id = [i[0] for i in c.fetchall()]

    # Get html code of all mates
    mates_list_html = users_lists_html(mates_id)

    # Cat all html code
    html = navigation_bar()
    html += '<h2> Mate List </h2>\n'
    html += mates_list_html
    return html


def search_user_page():
    # Generate html code for search name page
    user_id = parameters.getvalue('user_id')

    # Cat all html code
    html =  navigation_bar()
    html +=  '<form>\n'
    html += '<h2>Search User</h2>\n'
    html += '<div class="matelook_input">\n'
    # Post search string
    html += '<input type="text" name="requested_user_name">\n'
    # Keep track of user's id
    html += '<input type="hidden" name="user_id" value="{}">\n'.format(user_id)
    # Post a search parameter which tell the program to find matching results
    html += '<p>\n<input type="submit" value="search" >\n'
    # Keep user logged in
    html += '<input type="hidden" name="login" value=1>\n'
    html += '</div>\n'
    html += '<p>\n'
    html += '</form>\n'
    return html


def search_post_page():
    user_id = parameters.getvalue('user_id')
    html = navigation_bar()
    html += '<div class="matelook_input">\n'
    html += '<h2> Search Post </h2>\n'
    html += '<form>\n'
    # Post new parameter requested_post
    html += '<input type="text" name="requested_post">\n<p>\n'
    html += '<input type="submit" value="Search">\n'
    # Keep user logged in
    html += '<input type="hidden" name="login" value=1>\n'
    html += '<input type="hidden" name="user_id" value={}>'.format(user_id)
    html += '<form>\n'
    html += '</div>\n'
    return html


def edit_information_page():
    html = navigation_bar()
    user_id = parameters.getvalue("user_id")
    image_path = user_image_path(user_id)

    c.execute("SELECT * FROM userinfo WHERE user_id = {}".format(user_id))
    info = c.fetchone()

    html += '<div class="matelook_input" accpet=".jpg">\n'

    # html code for uploading user profile image
    html += '<img src={}><p>User image<p>\n'.format(image_path)
    html += '<form method="POST" enctype="multipart/form-data">\n'
    html += '<p><input type="file" name="filename"><p>\n'
    html += '<input type="submit" name="upload_image" value="Upload Image">\n'
    html += '</form>'

    # html code for text field to post new personal information
    html += '<form>\n'
    html += 'Name: <input type="text" name="edit_full_name" value="{}"><p>\n'.format(info[1])
    html += 'Birthday: <input type="text" name="edit_birthday" value={}><p>\n'.format(info[4])
    html += 'Program: <input type="text" name="edit_program" placeholder="YYYY-MM-DD" value={}><p>\n'.format(info[5])
    html += 'Suburb:  <input type="text" name="edit_home_suburb" value="{}"><p>\n'.format(info[6])
    html += 'Home latitude:  <input type="text" name="edit_home_lat" value={}><p>\n'.format(info[7])
    html += 'Home longitude:  <input type="text" name="edit_home_lon" value={}><p>\n'.format(info[8])
    html += '<input type="submit" name="EDIT_info">\n'
    html += '<input type="hidden" name="login" value=1>\n'
    html += '<input type="hidden" name="user_id" value={}>\n'.format(user_id)
    html += '<input type="hidden" name="home_page" value=1>\n'
    html += '</form>\n'
    html += '</div>\n'
    return html


def edit_information():
    user_id = parameters.getvalue("user_id")
    # Update each new value
    for key in parameters.keys():
        match = re.match("edit_(.+)", key)
        if match:
            update_column = match.group(1)
            new_data = parameters.getvalue(key)
            c.execute("UPDATE userinfo SET {} = '{}' WHERE user_id = {}".format(update_column, new_data, user_id))


def update_user_image():
    user_id = parameters.getvalue("user_id")
    if 'filename' in parameters:
        # Read uploaded file
        uploaded_file = parameters['filename'].file

        path = os.path.join(users_dir, 'z' + str(user_id))

        # For those new users who does not have a folder, create one
        if not os.path.exists(path):
            os.mkdir(path)

        # Check whether user has a profile image for now
        # If none, create a empty .jpg file
        path = os.path.join(users_dir, 'z' + str(user_id), 'profile.jpg')
        if not os.path.exists(path):
            open(path, 'a').close()
        else:
            os.remove(path)
            open(path, 'a').close()
        # Read bytes in the uploaded file and write them into the empty .jpg file
        b = bytes()
        for line in uploaded_file:
            b += line
        open(path, 'wb').write(b)


def matching_user_page():
    # Generate html code of search result page
    search_user_name = parameters.getvalue('requested_user_name')

    # Search for all of the users whose name contain user's input as a substring
    search_user_name = '%' + search_user_name + '%'
    c.execute('SELECT user_id FROM userinfo WHERE full_name LIKE ? ORDER BY user_id ASC', (search_user_name,))
    result = c.fetchall()

    html = navigation_bar()

    # If no matching record
    if not result:
        html += '<h2> No match result </h2>\n'
        return html
    else:
        # Convert user_ids from integer to string
        result_users_id = [str(i[0]) for i in result]

        html += '<h2> {} matching records </h2>\n'.format(str(len(result_users_id)))

        # Get html code for matching users and use pagination to show 3 results per page
        html += pagination(result_users_id, 'name')

        return html


def matching_post_page():
    # Get requested searching post from parameters
    post_content = parameters.getvalue('requested_post')
    html = navigation_bar()

    # Get all matching records from database
    search_string = '%' + post_content + '%'
    c.execute('SELECT * FROM posts WHERE content LIKE ?', (search_string,))
    matching_posts = c.fetchall()

    # Return if no matching record
    if not matching_posts:
        html += '<h2> No matching posts</h2>'
        return html

    html += '<h2> {} matching records </h2>\n'.format(str(len(matching_posts)))

    # Get html code for all posts and user pagination to show 3 results per page
    html += pagination(matching_posts, 'post')
    return html


def pagination(result_id, content_type):
    # Show 3 results per page
    n = 3

    # Show from (start) to (start + n)
    if 'start' in parameters.keys():
        start = int(parameters.getvalue('start')) + n
    else:
        start = 0

    # Get html code of all matching users/posts
    if content_type == 'name':
        html = users_lists_html(result_id[start:start + n])
    elif content_type == 'post':
        html = posts(result_id[start:start + n])

    # Center the buttons
    html += '<div class="matelook_button">\n'

    # If it is not the first page of result, add an button to redirect user to previous n results
    if start > 0:
        html += '<form>\n'
        html += '<input type="submit" name="previous" value="Show previous 3 results">\n'
        html += '<input type="hidden" name="start" value={}>\n'.format(str(start-2*n))
        # Go to search name page, search post page, user page or home page
        if 'requested_user_name' in parameters.keys():
            html += '<input type="hidden" name="requested_user_name" value={}>\n'.format(parameters.getvalue("requested_user_name"))
        elif 'requested_post' in parameters.keys():
            html += '<input type="hidden" name="requested_post" value={}>\n'.format(parameters.getvalue("requested_post"))
        elif 'page_user_id' in parameters.keys():
            html += '<input type="hidden" name="page_user_id" value={}>\n'.format(parameters.getvalue("page_user_id"))
        elif 'home_page' in parameters.keys():
            html += '<input type="hidden" name="home_page" value=1>\n'
        # Keep user logged in
        html += '<input type="hidden" name="login" value=1>\n'
        html += '<input type="hidden" name="user_id" value={}>\n'.format(parameters.getvalue('user_id'))
        html += '</form>\n'

    # If there is still remaining results to show, add an button to redirect user to next n results
    if len(result_id[start+n:]) > 0:
        html += '<form>\n'
        html += '<input type="submit" name="next" value="Show next 3 results">\n'
        html += '<input type="hidden" name="start" value={}>\n'.format(str(start))
        # Go to search name page, search post page, user page or home page
        if 'requested_user_name' in parameters.keys():
            html += '<input type="hidden" name="requested_user_name" value={}>\n'.format(parameters.getvalue("requested_user_name"))
        elif 'requested_post' in parameters.keys():
            html += '<input type="hidden" name="requested_post" value={}>\n'.format(parameters.getvalue("requested_post"))
        elif 'page_user_id' in parameters.keys():
            html += '<input type="hidden" name="page_user_id" value={}>\n'.format(parameters.getvalue("page_user_id"))
        elif 'home_page' in parameters.keys():
            html += '<input type="hidden" name="home_page" value=1>\n'
        # Keep user logged in
        html += '<input type="hidden" name="login" value=1>\n'
        html += '<input type="hidden" name="user_id" value={}>\n'.format(parameters.getvalue('user_id'))
        html += '</form>\n'
    html += '</div>\n'
    return html


def navigation_bar():
    # Generate html code for navigation bar which would be used in almost every page
    user_id = parameters.getvalue('user_id')
    page_user_id = parameters.getvalue("page_user_id")

    # Get the name of the logged in user
    c.execute('SELECT full_name FROM userinfo WHERE user_id = ?', (user_id,))
    user_full_name = c.fetchone()[0]

    html =  '<ul>\n'
    # Link to home page
    html += '<li><a href="matelook.cgi?user_id={}&login=1&home_page=1">Home</a></li>\n'.format(user_id)
    # Link to logged in user's personal page
    html += '<li><a href="matelook.cgi?user_id={}&login=1&page_user_id={}">{}</a></li>\n'.format(user_id, user_id, user_full_name)
    # Link to logged in user's mates list page
    html += '<li><a href="matelook.cgi?user_id={}&login=1&mates=1">Your Mates</a></li>\n'.format(user_id)
    # Link to mate's mates page
    if page_user_id and page_user_id != user_id:
        html += '<li><a href="matelook.cgi?user_id={}&login=1&matemates=1&page_user_id={}">His/Her Mates</a></li>\n'.format(user_id, page_user_id)
    # Link to search user page
    html += '<li><a href="matelook.cgi?search_name=1&login=1&user_id={}">Search User</a></li>\n'.format(user_id)
    # Link to search post page
    html += '<li><a href="matelook.cgi?search_post=1&login=1&user_id={}">Search Post</a></li>\n'.format(user_id)
    # Link to look at potential mates
    html += '<li><a href="matelook.cgi?mate_suggestion=1&login=1&user_id={}">Mates Suggestion</a></li>\n'.format(user_id)
    # Link to edit Information
    html += '<li><a href="matelook.cgi?edit_information=1&login=1&user_id={}">Edit Information</a></li>\n'.format(user_id)
    # Link to log out
    html += '<li><a href="matelook.cgi">Logout</a></li>\n'
    html += '</ul>\n'
    html += '<p>\n'
    return html


def users_lists_html(users_id):
    # Generate html code to show a list of user_ids
    html = ''
    user_id = parameters.getvalue('user_id')

    for u_id in users_id:
        # Get user image path
        image_path = user_image_path(u_id)

        # Get user full name from database
        c.execute('SELECT full_name FROM userinfo WHERE user_id = ?', (u_id, ))
        mate_name = c.fetchone()[0]
        html += '<p>\n'
        html += '<a href="matelook.cgi?user_id={}&page_user_id={}&login=1">\n'.format(user_id, u_id)
        html += '<p>\n'
        # Text link to user's personal page
        html += '<h2 {}\n'.format(mate_name)
        html += '</p>\n'
        # Image link to user's personal page
        html += '<img src={} class="matelook_mate_list">\n'.format(image_path)
        html += '</a>\n'
        html += '</p>\n'
        # Get html code to show user's details
        html += user_info(u_id)

        # Does not show "Follow" or "Unfollow" buttons if this is user himself/herself
        if u_id == user_id:
            continue

        # Follow and unfollow section
        html += follow_unfollow(u_id, user_id)
    return html


def user_image_path(user_id):
    # Find user image path
    image_path = os.path.join(users_dir, 'z' + str(user_id) + '/profile.jpg')
    # If user does not have a profile image, use default No_Image_Available.jpg which
    # has been stored in dataset-? folders
    if not os.path.isfile(image_path):
        image_path = os.path.join('No_Image_Available.jpg')
    return image_path


def user_info(user_id):
    # Retrive user info from datebase
    c.execute("SELECT * FROM userinfo WHERE user_id = ?", (user_id,))
    user_info = c.fetchone()
    (user_full_name, user_birthday, user_program, user_suburb) = (user_info[1], user_info[4], user_info[5], user_info[6])
    user_profile = user_info[9]

    # Generate html code for user details
    html = '<div class=matelook_user_details>\n'
    html += 'Name:{}\nId:{}\nBirthday:{}\nProgram:{}\nSuburb:{}\n'.format(user_full_name, 'z'+str(user_id), user_birthday,
                                                                                              user_program, user_suburb)
    # Show user profile if she/he has one
    if user_profile:
        html += 'Profile:{}\n'.format(user_profile)
    html += '</div>\n<p>\n'
    return html


def relation(mate_id, user_id):
    # Determine whether user is following a given mate
    c.execute("SELECT * FROM relations WHERE user_id = ? AND mate_id = ?", (user_id, mate_id))
    user_following_mate = c.fetchone()
    c.execute("SELECT * FROM relations WHERE user_id = ? AND mate_id = ?", (mate_id, user_id))
    mate_following_user = c.fetchone()

    # 4 Kinds of relations between users
    # Following of each other
    if user_following_mate and mate_following_user:
        return 0
    # User following mate while mate is not following user
    elif user_following_mate and not mate_following_user:
        return 1
    # Mate following user while user is not following mate
    elif not user_following_mate and mate_following_user:
        return 2
    # No relation
    else:
        return 3


def follow_unfollow(mate_id, user_id):
    html = '<div class="matelook_input">\n'
    html += '<form>\n'
    # Following each other
    if relation(mate_id, user_id) == 0:
        # Disabled button
        html += '<input type="submit" value="Mates Already" disabled>\n'
        html += '<input type="submit" name="unfollow" value="Unfollow">\n'
        html += '<input type="hidden" name="unfollow_mate_id" value={}>'.format(mate_id)
    # User following mate while mate is not following user
    elif relation(mate_id, user_id) == 1:
        html += '<input type="submit" value="You are following him/her" disabled>\n'
        html += '<input type="submit" name="unfollow" value="Unfollow">\n'
        html += '<input type="hidden" name="unfollow_mate_id" value={}>'.format(mate_id)
    # Mate following user while user is not following mate
    else:
        html += '<input type="submit" name="follow" value="Follow">\n'
        html += '<input type="hidden" name="follow_mate_id" value={}>'.format(mate_id)

    # Keep user logged in
    html += '<input type="hidden" name="login" value=1>\n'
    html += '<input type="hidden" name="user_id" value={}>'.format(user_id)
    # If user was looking at his/her mates page, direct user back to this page
    if 'mates' in parameters.keys():
        html += '<input type="hidden" name="mates" value="mates">\n'
    # If user was looking at his/her mate search result page, direct user back to this page
    elif 'requested_user_name' in parameters.keys():
        requested_user_name = parameters.getvalue('requested_user_name')
        html += '<input type="hidden" name="requested_user_name" value={}>'.format(requested_user_name)
    # If user was looking at his/her mate's personal page, direct user back to this page
    elif 'page_user_id' in parameters.keys():
        page_user_id = parameters.getvalue("page_user_id")
        html += '<input type="hidden" name="page_user_id" value={}>'.format(page_user_id)
    # If user was looking at his/her mate suggestion page, direct user back to this page
    elif 'mate_suggestion' in parameters.keys():
        html += '<input type="hidden" name="mate_suggestion" value=1>'
    html += '</form>\n'
    html += '</div>'
    return html


def insert_new_relation():
    user_id = parameters.getvalue('user_id')
    follow_mate_id = parameters.getvalue('follow_mate_id')
    # Insert new relation record into database
    c.execute("""INSERT INTO relations (user_id, mate_id)
                 VALUES (?, ?);
              """, (user_id, follow_mate_id))


def delete_existed_relation():
    user_id = parameters.getvalue('user_id')
    unfollow_mate_id = parameters.getvalue('unfollow_mate_id')
    # Delete existed relation from database
    c.execute(""" DELETE FROM relations WHERE user_id = ? AND mate_id = ?;
              """, (user_id, unfollow_mate_id))


def user_posts(post_user_id):
    # Retrieve user posts from database
    c.execute('SELECT * FROM posts where user_id = ? ORDER BY post_time DESC;', (post_user_id,))
    user_posts = c.fetchall()

    # Html for all user posts, including Date, time and post content
    html = pagination(user_posts, 'post')
    return html


def posts(posts_list):
    # Generate all posts html with a give list of posts
    user_id = parameters.getvalue('user_id')
    html = '<div class="matelook_user_posts_area">\n<p>\n'

    # Format of posts: (post_id, user_id, post_time, content)
    for post in posts_list:
        post_id, post_user_id, post_time, post_content = post

        # Convert integer to string
        post_id = str(post_id)
        post_user_id = str(post_user_id)

        # Convert time to a (Data:xxxx Time:xxxx) format
        post_time = re.sub('T', '<br>Time: ', post_time)

        # Since all message in database are encode in utf-8 standard
        post_content = post_content.decode('utf-8', 'strict')
        # Remove all '\\n'
        post_content = re.sub(r'\\n', '<br>\n', post_content)
        # One sentance a line
        post_content_lines = post_content.split('\n')

        # Get the post owner's full name
        c.execute("""SELECT userinfo.full_name
                  FROM userinfo JOIN posts ON userinfo.user_id=posts.user_id
                  WHERE posts.post_id = ?;""", (post_id,))
        post_user_full_name = c.fetchone()[0]

        # Generate html code for a single post which also includes the comments and replies under it
        html += '<div class="matelook_user_posts_content">\n'
        html += '<h3> User Post </h3>'
        # Href section
        html += '<a href="matelook.cgi?login=1&user_id={}&page_user_id={}">\n'.format(user_id, post_user_id)
        # Image link to post owner's personal page
        html += '<img src={} class="matelook_user_thumbnail_image">\n<br>\n'.format(user_image_path(post_user_id))
        # Text link to post owner's personal page
        html += '{}\n<br>\n'.format(post_user_full_name)
        html += '</a>\n'
        # Post date
        html += 'Date: {}<br>\n'.format(post_time)
        # Post contents
        html += 'Post:<br>\n'
        for line in post_content_lines:
            # Convert in line user_id into link of respective personal pages
            line = convert_id(line)
            html += '{}\n'.format(line)

        # Add comment section
        html += make_comment_or_reply('comment', post_id)

        # Delete post
        if int(post_user_id) == int(user_id):
            html += '<form>\n'
            html += '<input type="submit" name="delete_post" value="Delete post">\n'
            html += '<input type="hidden" name="delete_post_id" value={}>\n'.format(post_id)
            html += '<input type="hidden" name="login" value=1>\n'
            html += '<input type="hidden" name="user_id" value={}>\n'.format(user_id)
            html += '<input type="hidden" name="home_page" value=1>\n'
            html += '</form>\n'

        # html code of comment section
        html += '<br>\n<br><h4>All Comments Under This Post: </h4><br>\n'
        # Get html code for comment section
        html += comments(post_id)
        # End of one post
        html += '</div>\n<p>\n'
    # End of all posts
    html += '</div>\n<p>\n'
    return html


def comments(post_id):
    # Generate html code for all comments of a given post
    html = ''
    user_id = parameters.getvalue('user_id')
    page_user_id = parameters.getvalue('page_user_id')

    # Get all comments under a given post by using it's post id
    # All comments are sorted in the order of their time
    c.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY comment_time", (post_id,))
    user_comments = c.fetchall()

    # Format of comments: (comment_id, comment_user_id, post_id, comment_time, content)
    for comment in user_comments:
        comment_id, comment_user_id, post_id, comment_time, comment_content = comment

        # Decode comment content
        comment_content = comment_content.decode('utf-8')

        # Get correct format of a time
        comment_time = re.sub('T', '<br>Time: ', comment_time)

        # Get user full name from database
        c.execute("SELECT full_name FROM userinfo WHERE user_id = ?;", (comment_user_id,))
        comment_user_full_name = c.fetchone()[0]

        # Get user image path
        comment_user_image_path = user_image_path(str(comment_user_id))

        # html code for all a comment
        html += '<div class="matelook_user_posts_content">'
        html += '<a href="matelook.cgi?login=1&user_id={}&page_user_id={}">\n'.format(user_id, comment_user_id)
        # Image link to commenter's personal page
        html += '<img src={} class="matelook_user_thumbnail_image">\n<br>\n'.format(comment_user_image_path)
        # Text link to commenter's personal page
        html += comment_user_full_name + '<br>\n'
        html += '</a>\n'
        # Comment date
        html += 'Date: {}<br>\n'.format(comment_time)
        # Comment content
        html += 'Comment: {} <br>\n<br>\n'.format(convert_id(comment_content))

        # Add Reply section
        html += make_comment_or_reply('reply', comment_id)

        # Delete comment
        if int(comment_user_id) == int(user_id):
            html += '<form>\n'
            html += '<input type="submit" name="delete_comment" value="Delete comment">\n'
            html += '<input type="hidden" name="delete_comment_id" value={}>\n'.format(comment_id)
            html += '<input type="hidden" name="login" value=1>\n'
            html += '<input type="hidden" name="user_id" value={}>\n'.format(user_id)
            html += '<input type="hidden" name="home_page" value=1>\n'
            html += '</form>\n'

        # Reply section under this comment
        html += '<h4> All Replies Under This Comment: </h4>\n'
        html += '<div class="matelook_user_replies">'
        # Get html code for all replies under this comment
        html += replies(comment_id)
        html += '</div>'
        html += '</div>\n<p>\n'
    return html


def replies(comment_id):
    # Get all replies under a given comment
    c.execute('SELECT * FROM replies WHERE comment_id = ?', (comment_id,))
    user_replies = c.fetchall()
    # Return empty string if no comments
    if not user_replies:
        return ''

    user_id = parameters.getvalue('user_id')
    html = ''
    # Format of replies: (reply_id, user_id, comment_id, reply_time, content)
    for reply in user_replies:
        reply_id, reply_user_id, comment_id, reply_time, reply_content = reply
        # Decode
        reply_content = reply_content.decode('utf-8')
        # Get correct time format
        reply_time = re.sub('T', '<br>Time:', reply_time)
        # Get replier's name
        c.execute('SELECT full_name FROM userinfo WHERE user_id = ?', (reply_user_id,))
        reply_user_full_name = c.fetchone()[0]
        # Get replier's image path
        reply_user_image_path = user_image_path(str(reply_user_id))
        # html code for a reply
        html += '<div class="matelook_user_reply_content">\n'
        html += '<a href="matelook.cgi?login=1&user_id={}&page_user_id={}">\n'.format(user_id, reply_user_id)
        # Image link to the replier's personal page
        html += '<img src={} class="matelook_user_thumbnail_image">\n<br>\n'.format(reply_user_image_path)
        # Text link to the repliers' personal page
        html += reply_user_full_name + '<br>\n'
        html += '</a>\n'
        # Reply date
        html += 'Date: {}<br>\n'.format(reply_time)
        # Reply content
        html += 'Reply: {} <br>\n<br>\n'.format(convert_id(reply_content))
        html += '</div>\n'
        # Delete reply
        if int(reply_user_id) == int(user_id):
            html += '<form>\n'
            html += '<input type="submit" name="delete_reply" value="Delete reply">\n'
            html += '<input type="hidden" name="delete_reply_id" value={}>\n'.format(reply_id)
            html += '<input type="hidden" name="login" value=1>\n'
            html += '<input type="hidden" name="user_id" value={}>\n'.format(user_id)
            html += '<input type="hidden" name="home_page" value=1>\n'
            html += '</form>\n'
    return html


def convert_id(content):
    # Translate user id inside a message(post, comment or reply) into text link of it's owner's personal page

    user_id = parameters.getvalue('user_id')

    # Find all user_ids inside the message
    mentioned_users_id = re.findall('z(\d+)', content)
    # Return intact content if no user_ids inside the message
    if not mentioned_users_id:
        return content
    # Split content with user_ids as seperators
    splitted_content = re.split('z\d+', content)

    html = ''
    # Pop all user_ids and append them with splitted content alternatively
    # Number of user_id = Number of splitted content - 1
    while mentioned_users_id:
        m_user_id = mentioned_users_id.pop(0)
        # Get user full name from database by using the m_user_id(user_id of message owner)
        c.execute('SELECT full_name FROM userinfo WHERE user_id = ?', (m_user_id,))
        m_user_full_name = c.fetchone()[0]
        # Append next string from splitted content
        html += '{}'.format(splitted_content.pop(0))
        html += '<a href="matelook.cgi?login=1&page_user_id={}&user_id={}">\n'.format(m_user_id, user_id)
        # Text link to message owner's personal page
        html += '"{}"\n'.format(m_user_full_name)
        html += '</a>\n'
    html += '{}'.format(splitted_content.pop(0))
    return html


def update_profile():
    # Generate html code for update profile in home page
    user_id = parameters.getvalue('user_id')
    html = ''
    html += '<div class="matelook_input">\n'
    html += '<form>\n'
    # Use bigger input area
    html += '<textarea type="text" name="new_profile_text" cols="50" rows="8"></textarea>\n'
    # Post a new parameter "update_profile" to tell the program insert new profile into database
    html += '<p>\n<input type="submit" name="update_profile" value="Update your profile">\n'
    # Keep user logged in
    html += '<input type="hidden" name="login" value=1>\n'
    html += '<input type="hidden" name="user_id" value={}>\n'.format(user_id)
    # Redirect user to his/her personal page
    html += '<input type="hidden" name="page_user_id" value={}>\n'.format(user_id)
    html += '</form>'
    html += '</div>\n'
    return html


def make_post():
    # Generate html code for making post in home page
    user_id = parameters.getvalue('user_id')
    html = ''
    html += '<div class="matelook_input">\n'
    html += '<form>\n'
    # Use bigger input area
    html += '<textarea type="text" name="new_post_content" cols="80" rows="10"></textarea>\n'
    # Post a new parameter "make_post" to tell the program insert new post into database
    html += '<p>\n<input type="submit" value="Make Post">\n'
    # Keep user logged in
    html += '<input type="hidden" name="login" value=1>\n'
    html += '<input type="hidden" name="user_id" value={}>\n'.format(user_id)
    # Redirect user to home page
    html += '<input type="hidden" name="home_page" value=1>\n'
    html += '</form>'
    html += '</div>\n'
    return html


def make_comment_or_reply(message_type, father_message_id):
    user_id = parameters.getvalue('user_id')

    html = '<form>\n'
    # Text area for writing comment
    html += '<textarea type="text" name="new_{}_content" cols="60" rows="5"></textarea>\n<p>\n'.format(message_type)
    html += '<input type="submit" value="Post {}">\n'.format(message_type)
    # Keep user logged in
    html += '<input type="hidden" name="login" value=1>\n'
    html += '<input type="hidden" name="user_id" value={}>'.format(user_id)

    # If user is looking at someone's personal page, redirect user back to this personal page
    # after making a new comment
    if 'page_user_id' in parameters.keys():
        current_page_user_id = parameters.getvalue('page_user_id')
        html += '<input type="hidden" name="page_user_id" value={}>'.format(current_page_user_id)

    # If user is looking at matching result of his/her post search
    # Redirect user to the matching post result page
    elif 'requested_post' in parameters.keys():
        requested_post = parameters.getvalue('requested_post')
        html += '<input type="hidden" name="requested_post" value={}>'.format(requested_post)

    # Otherwise, redirect user back to homepage after making a new comment
    else:
        html += '<input type="hidden" name="home_page" value=1>'
    # Post a new parameter "make_comment" or "make_reply" to tell the program insert new post into database
    html += '<input type="hidden" name="make_{}" value=1>\n'.format(message_type)
    html += '<input type="hidden" name="father_message_id" value={}>\n'.format(father_message_id)
    html += '</form>\n'
    return html


def delete_message():
    # Delete post
    if 'delete_post_id' in parameters.keys():
        delete_post_id = parameters.getvalue("delete_post_id")

        # Get all comments under this post
        c.execute("SELECT comment_id FROM comments WHERE post_id = {}".format(delete_post_id))
        comments_under_this_post = c.fetchall()
        for comment in comments_under_this_post:
            delete_comment_id = comment[0]

            # Get all replies under this comment
            c.execute("SELECT reply_id FROM replies WHERE comment_id = {}".format(delete_comment_id))
            replies_under_this_comment = c.fetchall()
            for reply in replies_under_this_comment:
                delete_reply_id = reply[0]
                # Delete this reply
                c.execute("DELETE FROM replies WHERE reply_id = {}".format(delete_reply_id))
                # Delete this comment
            c.execute("DELETE FROM comments WHERE comment_id = {}".format(delete_comment_id))
            # Delete this post
        c.execute('DELETE FROM posts WHERE post_id = "{}"'.format(delete_post_id))

    # Delete comment
    elif 'delete_comment_id' in parameters.keys():
        delete_comment_id = parameters.getvalue("delete_comment_id")

        # Get all replies under this comment
        c.execute("SELECT reply_id FROM replies WHERE comment_id = {}".format(delete_comment_id))
        replies_under_this_comment = c.fetchall()
        for reply in replies_under_this_comment:
            delete_reply_id = reply[0]
            # Delete this reply
            c.execute("DELETE FROM replies WHERE reply_id = {}".format(delete_reply_id))
            # Delete this comment
        c.execute('DELETE FROM comments WHERE comment_id = {}'.format(delete_comment_id))

    # Delete reply
    elif 'delete_reply_id' in parameters.keys():
        delete_reply_id = parameters.getvalue("delete_reply_id")
        c.execute('DELETE from replies WHERE reply_id = "{}"'.format(delete_reply_id))

    # Database commit change
    conn.commit()


def insert_new_message(message_type):
    # After user has made a new post, comment or reply, insert this new message into database
    user_id = parameters.getvalue('user_id')

    if message_type == 'post':
        # Encode post content
        post_content = parameters.getvalue('new_post_content').encode(encoding='utf-8')
        # Get next post id for the latest post
        c.execute("SELECT max(post_id) FROM posts;")
        post_id = int(c.fetchone()[0]) + 1
        # Make sure the time string is in the same format as those in database
        post_time = re.sub('\.\d+', '+0000', datetime.datetime.now().isoformat())
        # SQL command to insert new record
        c.execute("""INSERT INTO posts (post_id, user_id, post_time, content)
                     VALUES (?, ?, ?, ?);
                """, (post_id, user_id, post_time, post_content))
    else:
        # Get father message id and type
        father_message_id = parameters.getvalue('father_message_id')
        # If new message type is comment then it's father message type is post
        # If new message type is reply then it's father message type is comment
        father_message_type = 'post' if message_type == 'comment' else 'comment'

        table_name = 'comments' if message_type == 'comment' else 'replies'

        # Encode message content
        message_content = parameters.getvalue('new_{}_content'.format(message_type)).encode(encoding='utf-8')

        # Get next (comment/reply) id for the latest post
        c.execute("SELECT max({}_id) FROM {};".format(message_type, table_name))
        message_id = int(c.fetchone()[0]) + 1

        # Make sure the time string is in the same format as those in database
        message_time = re.sub('\.\d+', '+0000', datetime.datetime.now().isoformat())

        # SQL command to insert new record
        c.execute("""INSERT INTO {} ({}_id, user_id, {}_id, {}_time, content)
                     VALUES (?, ?, ?, ?, ?);
                """.format(table_name, message_type, father_message_type, message_type),
                  (message_id, user_id, father_message_id, message_time, message_content))


def mate_suggestion(user_id):
    # Use a counter to build a credit system
    potential_mates = collections.defaultdict(list)

    user_id = int(user_id)

    # Find potential mates enrolled in same course
    c.execute("SELECT course FROM enrollments WHERE user_id = '{}'".format(user_id))
    enrolled_courses = c.fetchall()
    enrolled_courses = [i[0] for i in enrolled_courses]

    # One credit for one common course
    for course in enrolled_courses:
        c.execute("SELECT user_id FROM enrollments WHERE course = '{}' AND user_id != '{}'".format(course, user_id))
        enrolled_students = c.fetchall()
        enrolled_students = [i[0] for i in enrolled_students]
        for potential_mate_id in enrolled_students:
            if potential_mate_id == user_id:
                continue
            # Only select those who are not user's current mate
            c.execute("SELECT mate_id FROM relations WHERE mate_id = '{}' AND user_id = '{}'".format(potential_mate_id, user_id))
            if not c.fetchone():
                potential_mates[potential_mate_id].append(course)

    # Find potential mates of current mates
    c.execute("SELECT mate_id FROM relations WHERE user_id = '{}'".format(user_id))
    mates_id = c.fetchall()
    mates_id = [i[0] for i in mates_id]

    # One credit for each appearance in current mate's mate list
    for m_id in mates_id:
        c.execute("SELECT mate_id FROM relations WHERE user_id = '{}'".format(m_id))
        mates_of_mate = c.fetchall()
        mates_of_mate = [i[0] for i in mates_of_mate]
        for potential_mate_id in mates_of_mate:
            if potential_mate_id == user_id:
                continue
            # Only select those who are not user's current mate
            c.execute("SELECT mate_id FROM relations WHERE mate_id = '{}' AND user_id = '{}'".format(potential_mate_id, user_id))
            if not c.fetchone():
                potential_mates[potential_mate_id].append(m_id)

    # Only select the top 5 potential mates
    top_5 = sorted(potential_mates.items(), key=lambda item: len(item[1]) , reverse=True)[:5]
    return top_5


def mate_suggestion_page():
    user_id = parameters.getvalue("user_id")

    # Get the IDs and commonness of potential mates
    # (mate_id, [list of common courses and common mates])
    potential_mates_id_and_commoness = mate_suggestion(user_id)

    html = navigation_bar()

    html += '<div class="matelook_input">'
    # Print out every potential mates' user info and commonness between user and him/her
    for i in potential_mates_id_and_commoness:
        potential_mates_id, commonness = i
        html += '<img src={}>'.format(user_image_path(potential_mates_id))
        html += user_info(potential_mates_id)
        common_courses, common_mates = find_commonness(commonness)
        if common_courses:
            html += '<h3> You are both enrolled in: {} </h3>'.format(str.join(', ', common_courses))
        if common_mates:
            html += '<h3> Mates of yours are following him/her: {} </h3>'.format(convert_id(str.join(', ', common_mates)))
        html += follow_unfollow(potential_mates_id, user_id)
    html += '</div>'

    return html


def find_commonness(commonness):
    common_courses = []
    common_mates = []
    # Put all common mates in a list
    [common_mates.append('z' + str(c)) for c in commonness if re.match("^\d{7}$", str(c))]
    # Put all common courses in a list
    [common_courses.append(c) for c in commonness if not re.match("^\d{7}$", str(c))]
    return common_courses, common_mates


def page_header():
    return """Content-Type: text/html;charset=utf-8

<!DOCTYPE html>
<html lang="en_AU">
<head>
<title>matelook</title>
<link href="matelook.css" rel="stylesheet">
</head>
<body>
<div class="matelook_heading">
matelook
</div>
"""


def page_trailer():
    html = ""
    if debug:
        html += "".join("<!-- %s=%s -->\n" % (p, parameters.getvalue(p)) for p in parameters)
    html += "</body>\n</html>"
    return html

if __name__ == '__main__':
    conn = sqlite3.connect('matelook.db')
    c = conn.cursor()
    debug = 1
    sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer)
    main()
    conn.commit()