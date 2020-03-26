import os
import webapp2
from google.appengine.ext import db
from google.appengine.api import memcache
from bcrypt import bcrypt
import jinja2
import datetime
import re
import json
import logging
import time


#jinja file position and enviorment
template_dir=os.path.join(os.path.dirname(__file__), 'static/html')
jinja_env = jinja2.Environment(autoescape=True,loader=jinja2.FileSystemLoader(template_dir))

title='Title'
USER_RE= re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE= re.compile(r"^.{3,20}$")
EMAIL_RE= re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def secure_pw(pw,n_salt=1):
    return bcrypt.hashpw(pw, bcrypt.gensalt(n_salt)).split('$')[-1]

def validate_secure_pw(pw,h,n_salt):
    aux='$2a$%02d$' % n_salt + h
    try:
        if bcrypt.hashpw(pw, aux)==aux:
            return True
        else:
            return False
    except:
        return False

def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

def memcaching(update=False):
    bposts=memcache.get('front10')
    if bposts is None or update is True:
        bposts=db.GqlQuery("SELECT * FROM BlogPosts ORDER BY created DESC LIMIT 10")
        logging.warning("DB HIT")
        memcache.set('front10',list(bposts))
    return bposts

def initialize(PageHand,block=True):
    cuser_id=PageHand.request.cookies.get('user_id')
    if cuser_id is None:
        PageHand.redirect('/blog/login')
    cuser_id=cuser_id.split('|')
    if len(cuser_id)==2:
        if validate_secure_pw(cuser_id[0],cuser_id[1],1)==True:
            return cuser_id[0]
    if block is True:
        PageHand.redirect('/blog/login')
        
class Users(db.Model):
    user=db.StringProperty(required=True)
    password=db.StringProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)
    email=db.EmailProperty()

class BlogPosts(db.Model):
    subject=db.StringProperty(required=True)
    content=db.TextProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)
    lastmodified=db.DateTimeProperty(auto_now=True)

#PAGINATION HANDLERS


class Handler(webapp2.RequestHandler):
    def write_html_page(self,html_file,template_values):
        template = jinja_env.get_template(html_file)
        self.response.out.write(template.render(template_values))
        
    def write_jason_page(self,out_json):
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.response.out.write(json.dumps(out_json,indent=4,sort_keys=True))
       
class MainPage(Handler):
    def get(self):
        bposts=memcaching()
        username=initialize(self,False)
        self.write_html_page('index.html',{'title':title,'logname':username,'bposts':bposts})

            

class MainJSON(Handler):
    def get(self):
        initialize(self)
        bposts=db.GqlQuery("SELECT * FROM BlogPosts ORDER BY created DESC")
        list=[]
        for post in bposts:
            list.append({'subject':post.subject, 'content':post.content, 'created':post.created.strftime("%a %b %d %H:%M:%S %Y"), 'last_modified': post.lastmodified.strftime("%a %b %d %H:%M:%S %Y")})
        self.write_jason_page(list)
        
class SignupPage(Handler):
    def get(self):
        self.write_html_page('signup.html',{'title':title})
        
    def post(self):
        inusername=self.request.get("username")
        inpassword=self.request.get("password")
        inveripassword=self.request.get("verify")
        inemail=self.request.get("email")

        #validate inputed data
        usererror=""
        passerror=""
        vpasserror=""
        emailerror=""
        flag=0

        if not valid_username(inusername):
            usererror="That's not a valid username."
            flag=flag+1

        if not valid_password(inpassword):
            passerror="That's not a valid password"
            flag=flag+1

        elif inpassword!=inveripassword:
            vpasserror="Your passwords didn't match"
            flag=flag+1
       
        if not valid_email(inemail):
            emailerror="That's not a valid email"
            flag=flag+1
        
        if not db.GqlQuery("Select * from Users where user=:1",inusername).get()==None:
            usererror="That username already exists, choose another one."
            flag=flag+1
        
        if flag==0:
            if len(inemail)==0:
                newuser=Users(user=inusername, password=secure_pw(inpassword,n_salt=2))
            else:
                newuser=Users(user=inusername, password=secure_pw(inpassword,n_salt=2),email=inemail)   
            newuser.put() # inserting into database
            #create cookie
            self.response.headers.add_header('Set-Cookie', 'user_id=%s|%s; Path=/' % (str(inusername),secure_pw(inusername,1)))
            self.redirect("/blog")
        else:
            self.write_html_page('signup.html',{'title':title,'user_error':usererror,'pass_error':passerror, 'vpass_error':vpasserror, 'email_error':emailerror, 'inuser':inusername,'inpass':inpassword,'vinpass':inveripassword,'inemail':inemail})
           
class LoginPage(Handler):
    def get(self):
        self.write_html_page('login.html',{'title':title,'error':''})
        
    def post(self):
        inusername=self.request.get("username")
        inpassword=self.request.get("password")
        
        dbuser=db.GqlQuery("Select * from Users where user=:1",inusername).get()
        if not dbuser==None:
            if validate_secure_pw(inpassword,dbuser.password,2)==True:
                self.response.headers.add_header('Set-Cookie', 'user_id=%s|%s; Path=/' % (str(inusername),secure_pw(inusername,1)))
                self.redirect("/blog")
        
        self.write_html_page('login.html', {'title':title,'user':inusername, 'error':'Invalid username or password.'})
              
class NewpostPage(Handler):
    def get(self):
        self.write_html_page('newpost.html',{'title':title,'error':''})
    
    def post(self):
        insubject=self.request.get('subject')
        incontent=self.request.get('content')
          
        if len(insubject)==0 or len(incontent)==0:
            self.write_html_page('newpost.html',{'title':title,'subject':insubject,'content':incontent,'error':'Enter a subject and content please'})
        else:
            newpost=BlogPosts(subject=insubject,content=incontent)
            newpost.put()
            memcaching(update=True) 
            self.redirect('/blog/%d'% newpost.key().id())
        
class PermalinkPage(Handler):
    def get(self,post_id):
        permapost=memcache.get('perma'+post_id) # lookup in cache
        if permapost is None:
            permapost=BlogPosts.get_by_id(int(post_id))
            logging.warning("DB HIT")
            if permapost is not None:
                memcache.set('perma'+post_id, permapost)
            else:
                self.abort(404)             
        
        self.write_html_page('permalink.html', {'title':title, 'post':permapost, 'logname':initialize(self,False)})
        
class PermalinkJSON(Handler):
    def get(self,post_id):
        initialize(self)
        post=BlogPosts.get_by_id(int(post_id))
        if not post==None:
            self.write_jason_page({'subject':post.subject, 'content':post.content, 'created':post.created.strftime("%a %b %d %H:%M:%S %Y"), 'last_modified': post.lastmodified.strftime("%a %b %d %H:%M:%S %Y")})
        else:
            self.abort(404)

        
class Logout(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % '')
        self.redirect('/blog')    

class FlushCache(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect('/blog')

   
app=webapp2.WSGIApplication([('/blog/?',MainPage),
                             ('/blog/?\.json',MainJSON),
                             ('/blog/signup/?',SignupPage),
                             ('/blog/newpost/?',NewpostPage),
                             ('/blog/login/?',LoginPage),
                             ('/blog/(\d+)/?',PermalinkPage),
                             ('/blog/logout/?',Logout),
                             ('/blog/(\d+)\.json/?',PermalinkJSON),
                             ('/blog/flush/?',FlushCache)],
                             debug=True)

