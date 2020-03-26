import os
import webapp2
from google.appengine.ext import db
from google.appengine.api import memcache
from bcrypt import bcrypt
import jinja2
import json
import re
import logging
import time
import security
import datamodels


#jinja file position and enviorment
template_dir=os.path.join(os.path.dirname(__file__), 'static/html')
jinja_env = jinja2.Environment(autoescape=True,loader=jinja2.FileSystemLoader(template_dir))




#General Utils Class
class Handler(webapp2.RequestHandler):
   
    #jinja html template write
    def write_html_page(self,html_file,template_values={}):
        self.response.headers['Content-Type']= "text/html"
        template = jinja_env.get_template(html_file)
        self.response.out.write(template.render(template_values))
    
    #writing json from ajax requests
    def write_json_data(self,data):
        self.response.headers['Content-Type']="application/json"
        self.response.out.write(json.dumps(data))
        
    #string write function
    def printpage(self,s):
        self.response.headers['Content-Type']='text/plain'
        self.response.out.write(s)
    
    def get_cookie(self,cookie_name):
        return self.request.cookies.get(cookie_name)
    
    def set_cookie(self,cookie_name,cookie_val='',cookie_path='/'):
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=%s' % (cookie_name,cookie_val,cookie_path))
           

class SignupPage(Handler):
    path='/'
    def get(self):
        self.write_html_page("signuppage.html")
        
    def post(self):
        errorflag=False
        username_error=""
        password_error=""
        verify_error=""
        email_error=""
        
        inusername=self.request.get("username")
        inpassword=self.request.get("password")
        inverify=self.request.get("verify")
        inemail=self.request.get("email")

        
        if not db.GqlQuery("Select * from Users where username=:1",inusername).get()==None:
            username_error="That Username is already in use, choose another one"
            errorflag=True
        
        if not security.valid_username(inusername):
            username_error="Invalid Username"
            errorflag=True
        
        
        if not security.valid_password(inpassword):
            password_error="Invalid Password"
            errorflag=True
        
        if not inpassword==inverify:
            verify_error="The Password don't match"
            errorflag=True
            
        if not security.valid_email(inemail):
            email_error="Invalid Email"
            errorflag=True
        
        
        
        if errorflag==False:
            if len(inemail)==0:
                inemail=None
            newuser=datamodels.Users(username=inusername,password=security.secure_pw(inpassword,2),email=inemail)
            newuser.put() # inserting into database
            #setting cookie and redirecting
            self.set_cookie('user_id', security.secure_cookie(str(newuser.key()),2))
            self.redirect(SignupPage.path)
        else:
            self.write_html_page("signuppage.html", {"user_error":username_error,"inuser":inusername,"pass_error":password_error,"inpass":inpassword,"vpass_error":verify_error,"vinpass":inverify,"email_error":email_error,"inemail":inemail})
            
                           
class LoginPage(Handler):
    path="/"
    def get(self):
        self.write_html_page("loginpage.html")
        
        
    def post(self):
        inusername=self.request.get("username")
        inpassword=self.request.get("password")

        userfd=db.GqlQuery("Select * from Users where username=:1",inusername).get()
    
        if userfd:
            if security.validate_secure_pw(inpassword,userfd.password):
                self.set_cookie('user_id', security.secure_cookie(str(userfd.key()),2))
                self.redirect(LoginPage.path)
        
        self.write_html_page("loginpage.html", {"error":"Incorrect Username or Password","user":inusername})
        


class Logout(Handler):
    def get(self):
        self.set_cookie("user_id")
        self.redirect(self.request.referer)  

   
class EditPage(Handler):
    def get(self,inurl):
        userkey=security.validate_secure_cookie(self.get_cookie('user_id'))
        wikipg=db.GqlQuery("SELECT * FROM WikiPages WHERE pageurl=:1 ORDER BY created DESC",inurl)
        count=wikipg.count()
        try:
            version=int(self.request.GET['v'])
        except:
            version=0
        
        if userkey:
            if count>0 and version<count:
                self.write_html_page("editpage.html",{"logname":db.get(userkey).username,"url":inurl,"content":wikipg[int(version)].pagecontent})
            else:
                self.write_html_page("editpage.html",{"logname":db.get(userkey).username,"url":inurl})
        else:
            self.redirect('/login')
          
           
    def post(self,inurl):
        incontent=self.request.get("content")
        newwikipg=datamodels.WikiPages(pageurl=inurl,pagecontent=incontent)
        newwikipg.put()
        self.redirect(inurl)
        
    
        
        

class WikiPage(Handler):
    def get(self,inurl):
        userkey=security.validate_secure_cookie(self.get_cookie('user_id'))
        wikipg=db.GqlQuery("SELECT * FROM WikiPages WHERE pageurl=:1 ORDER BY created DESC",inurl)
        count=wikipg.count()
        try:
            version=int(self.request.GET['v'])
        except:
            version=0
        
        
        if count>0:
            if userkey:
                self.write_html_page("wikipage.html",{"logname":db.get(userkey).username,"url":inurl,"content":wikipg[int(version)].pagecontent})
            else:
                self.write_html_page("wikipage.html",{"logname":None,"url":inurl,"content":wikipg[int(version)].pagecontent})
        else:  
            self.redirect('/_edit'+inurl)
       


class HistoryPage(Handler):
    def get(self,inurl):
        userkey=security.validate_secure_cookie(self.get_cookie('user_id'))
        wikipg=db.GqlQuery("SELECT * FROM WikiPages WHERE pageurl=:1 ORDER BY created DESC",inurl)
        
        if userkey:
            self.write_html_page("historypage.html",{"logname":db.get(userkey).username,"url":inurl,"wikipg":wikipg})
        else:
            self.write_html_page("historypage.html", {"logname":None,"url":inurl,"wikipg":wikipg})
        
        
class  ColdStart(Handler):
    def get(self):
        newwikipg=datamodels.WikiPages(pageurl='/',pagecontent="Coldstarted....")
        newwikipg.put()
        
        
        
         


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app=webapp2.WSGIApplication([('/signup/?',SignupPage),
                             ('/login/?',LoginPage),
                             ('/logout/?',Logout),
                             ('/coldstart/?',ColdStart),
                             ('/_history'+PAGE_RE,HistoryPage),
                             ('/_edit'+PAGE_RE,EditPage),
                             (PAGE_RE, WikiPage)],
                             debug=True)


           
           
           
           
           
           
           
