from flask import Flask, redirect,render_template, request,redirect
from pandas import DataFrame



app = Flask(__name__)

app.config['data']="static/"
@app.route("/",methods=['GET','POST'])
def hello_world():
    if request.method=="POST":
        username=request.form['username']
        message=request.form['message']
        f=open(app.config['data']+"data.txt","a")
        f.write(username+","+message+"\n")
        dat=open(app.config['data']+"data.txt","r").read().split("\n")
        user_data=[x.split(",")[1] for x in dat if x.split(",")[0] == username]
        user_data.append(message)
        return render_template('index.html', result=user_data,username=username)

        
    return render_template('index.html', result=None)
        
if __name__ == "__main__":
    app.run(debug=True)