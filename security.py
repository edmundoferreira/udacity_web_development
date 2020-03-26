from bcrypt import bcrypt
import re

USER_RE= re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE= re.compile(r"^.{3,20}$")
EMAIL_RE= re.compile(r"^[\S]+@[\S]+\.[\S]+$")


#Regex funcitons for common fields
def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)



#Hassing Functions
def secure_pw(pw,n_salt=2):
    try:
        return bcrypt.hashpw(pw, bcrypt.gensalt(n_salt)).split('$')[-1]
    except:
        return None
            
def validate_secure_pw(pw,h,n_salt=2):
    version_append='$2a$%02d$' % n_salt + h
    try:
        if bcrypt.hashpw(pw, version_append)==version_append:
            return True
        else:
            return None
    except:
        return None

def secure_cookie(cookie_val,n_salt=2):
    try:
        bcr_hash= bcrypt.hashpw(cookie_val, bcrypt.gensalt(n_salt)).split('$')[-1]+ '.'+cookie_val
        return bcr_hash
    except:
        return None

def validate_secure_cookie(h,n_salt=2):
    if h:
        cookie_val=h.split('.')[-1]
        h=h[:-len(cookie_val)-1]
        version_append='$2a$%02d$' % n_salt + h
        try:
            if bcrypt.hashpw(cookie_val, version_append)==version_append:
                return cookie_val
            else:
                return None
        except:
            return None
    else:
        return None
            



