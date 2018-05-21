from flask import Flask, render_template, request, redirect, jsonify,flash, url_for,abort, g
from sqlalchemy import create_engine,or_
from sqlalchemy.orm import sessionmaker
#from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session
from findARestaurant import findARestaurant
from model import Base, User,Request, Proposal,MealDate
engine = create_engine('sqlite:///data.db')

from geocode import getGeocodeLocation
import httplib2
from flask import make_response
import requests
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()
Base.metadata.bind = engine
#DBSession = sessionmaker(bind=engine)
#session =DBSession()
session = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)
app.secret_key = 'super secret key'

@auth.verify_password
def verify_password(username_or_token, password):
    #Try to see if it's a token first
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(email = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True
@app.route('/',methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form['Email']
        password=request.form['Password']
        #if user is None:
         #3  flash('this username not exist')
          # return render_template('Login.html')
        if verify_password(email,password):
            user=exist=session.query(User).filter_by(email=email).first()
            return redirect(url_for('userpage',id=user.id))
        else:
            flash('password or username is wrong')
            return render_template('Login.html')
    else:
        return render_template('Login.html')

@app.route('/newUser',methods=['POST','GET'])
def CreateUser():
    if request.method=="POST":
        if request.form['Email'] and request.form['Password']:
            Email= request.form['Email']
            Password=request.form['c-Password']
            CPassword=request.form['Password']
            if (Password==CPassword):
               exist=session.query(User).filter_by(email=Email).first()
               if  exist is None:
                   user=User(email=Email)
                   user.hash_password(Password)
                   session.add(user)
                   session.commit()
                   return redirect(url_for('login'))
               else:
                    flash('this email already exist')
                    return render_template('CreateNewUser.html')
            else:
                 flash('the password is not same as comfirm password')
                 return render_template('CreateNewUser.html')
    else:
        return render_template('CreateNewUser.html')

@app.route('/user/<int:id>',methods=['POST','GET'])
@auth.login_required
def userpage(id):
    #if request.method == 'POST':
     #    location=request.form['location']
      #   meat=request.form['meat']
       #  print "ell"
        # return redirect(url_for('searchLocation',location=location,meat=meat))
    #else:
       # return render_template('search.html',location="")
       user = session.query(User).filter_by(id=id).first()
      # proposals=session.query(Proposal).filter(or_(Proposal.user_proposed_to==id,Proposal.user_proposed_from==id)).all()
       requests=session.query(Request).filter(Request.user_id!=id).all()
       userrequest=session.query(Request).filter(Request.user_id==id).all()
       return render_template('Userpage.html',user=user,requests=requests,userrequest=userrequest)
@app.route('/user/<int:request_id>/propsal/meet/<int:user_proposed_from>&<int:user_proposed_to>',methods=['POST','GET'])
def meet(user_proposed_from,user_proposed_to,request_id):
    user=session.query(User).filter_by(id=user_proposed_from).first()
    user2=session.query(User).filter_by(id=user_proposed_to).first()
    proposal=Proposal(request_id=request_id)
    proposal.user_proposed_from=user_proposed_from
    proposal.user_proposed_to=user_proposed_to
    session.add(proposal)
    session.commit()
    return render_template('meet.html',user=user,user2=user2)
@app.route('/user/<int:id>/propsal',methods=['POST','GET'])
def proposal(id):
    proposals=session.query(Proposal).filter_by(user_proposed_to=id).all()
    user=session.query(User).filter_by(id=id).first()
    users=session.query(User).all()
    return render_template('proposal.html',proposals=proposals,id=id,user=user,users=users)
@app.route('/user/<int:id>/<int:proposal_id>',methods=['POST','GET'])
def agree(proposal_id,id):
    proposal=session.query(Proposal).filter_by(id=proposal_id).first()
    user_1=session.query(User).filter_by(id=proposal.user_proposed_to).first()
    user_2=session.query(User).filter_by(id=proposal.user_proposed_from).first()
    request=session.query(Request).filter_by(id=proposal.request.id).first()
    restaurant_info=findARestaurant(request.meal_type,request.location_string)
    meatdata=MealDate()
    meatdata.user_1=user_1.id
    meatdata.user_2=user_2.id
    meatdata.restaurant_name=restaurant_info['name']
    meatdata.restaurant_address=restaurant_info['address']
    meatdata.meal_time=request.meal_time
    session.add(meatdata)
    session.commit()
    return render_template('agree.html',user=user_1)
    #return str(meatdata.user_1)
@app.route('/user/<int:id>/check',methods=['POST','GET'])
def Checktheproposal(id):
    proposals=session.query(Proposal).filter_by(user_proposed_from=id).all()
    user=session.query(User).filter_by(id=id).first()
    return render_template('check.html',proposals=proposals,id=id,user=user)
@app.route('/user/<int:id>/date',methods=['POST','GET'])
def showyourdate(id):
    #3mealDates1=session.query(MealDate).filter(MealDate.user_1==id)
    mealDates1=session.query(MealDate.id,MealDate.meal_time,MealDate.restaurant_name,MealDate.restaurant_address,User.email).filter(MealDate.user_1==id).filter(MealDate.user_2==User.id)
    mealDates2=session.query(MealDate.id,MealDate.meal_time,MealDate.restaurant_name,MealDate.restaurant_address,User.email).filter(MealDate.user_2==id).filter(MealDate.user_1==User.id)
    #mealDates=session.query(MealDate).all()
    user=session.query(User).filter_by(id=id).first()
    #user2=session.query(User).all()
    #name=mealDates.restaurant_name
    #print mealDates.resturant_name
    return render_template('showYourDate.html',mealDates1=mealDates1,id=id,user=user,mealDates2=mealDates2)
    #return str(len(mealDates))
@app.route('/user/<int:id>/makeRequest',methods=['POST','GET'])
def Makerequest(id):
    user = session.query(User).filter_by(id=id).first()
    if request.method=='POST':
        location=request.form['location']
        if location=="" or request.form['meal_type']==""or request.form['date']=="" or request.form['time']=="":
           flash('this two input should not be empty')
           return render_template('RequestPage.html',user=user)
        latitude,longitude=getGeocodeLocation(location)
        if latitude=="zero":
           flash('Sorry,can not find your location')
           return render_template('RequestPage.html',user=user)
        restaurant_info=findARestaurant(request.form['meal_type'],location)
        if restaurant_info=="No Restaurants Found":
           flash('Sorry,can not find the target restaurant according your meal type')
           return render_template('RequestPage.html',user=user)
        meal_time=request.form['date']+request.form['time']
        Re=Request(user_id=id)
        Re.meal_type=request.form['meal_type']
        Re.latitude=latitude
        Re.longitude=longitude
        Re.location_string=location
        session.add(Re)
        session.commit()
        return render_template('RequestPage.html',user=user)
    else:
        return render_template('RequestPage.html',user=user)
@app.route('/user/<int:id>/<int:proposal_id>/delete',methods=['POST','GET'])
def deleteproposal(id,proposal_id):
    user=session.query(User).filter_by(id=id).first()
    proposalToDelete=session.query(Proposal).filter_by(id=proposal_id).one()
    session.delete(proposalToDelete)
    session.commit()
    return redirect(url_for('userpage',id=id))
@app.route('/user/<int:id>/request/<int:request_id>/delete',methods=['POST','GET'])
def deleterequest(id,request_id):
    user=session.query(User).filter_by(id=id).first()
    requestToDelete=session.query(Request).filter(Request.id==request_id).one()
    proposalToDelete=session.query(Proposal).filter(Proposal.request_id==request_id).all()
    for x in proposalToDelete:
        session.delete(x)
    session.delete(requestToDelete)
    session.commit()
    return redirect(url_for('userpage',id=id))
@app.route('/user/<int:id>/date/<int:date_id>/delete',methods=['POST','GET'])
def deleteDate(id,date_id):
    user=session.query(User).filter_by(id=id).first()
    DateToDelete=session.query(MealDate).filter(MealDate.id==date_id).one()
    session.delete(DateToDelete)
    session.commit()
    return redirect(url_for('userpage',id=id))

@app.route('/search/<location>/<meat>',methods=['POST','GET'])
def searchLocation(location,meat):
    restaurant_info=findARestaurant(meat,location)
    return restaurant_info['name']

if __name__ == '__main__':
     app.run('127.0.0.1', 5000, debug=True)
