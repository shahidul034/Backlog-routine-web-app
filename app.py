from inspect import currentframe
from flask import Flask, redirect, render_template, request, redirect
import os
import csv
import pandas as pd
from flask import send_file


app = Flask(__name__)

# Creating the upload folder
upload_folder = "uploads/"
save_routine = "save_routine/"
if not os.path.exists(upload_folder):
    os.mkdir(upload_folder)
if not os.path.exists(save_routine):
    os.mkdir(save_routine)

app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SAVE_ROUTINE'] = save_routine


def get_linenumber():
    cf = currentframe()
    print(f"line: {cf.f_back.f_lineno}-----------------------")


sep = "|"


def roll_return(temp):
    temp2 = ""
    for x in temp:
        if x == "(":
            break
        else:
            temp2 += x
    temp2 = temp2.split(",")
    temp2 = [x.replace(" ", "").replace("\n", "") for x in temp2]
    return sep.join(temp2)


def course_name_return(st):
    temp = ""
    flag = 0
    for x in st:
        if x == ')':
            flag = 1
        elif flag == 1:
            temp += x
    temp = temp.replace("\n", " ").split(" ")
    temp = [x for x in temp if x != ""]
    return ' '.join(temp)


def return_credit(txt):
    import re
    x = re.search("[(].*[)]", txt)
    credit = (x.group().replace("(", "").replace(')', ""))
    return credit


def course_code_return(st):
    temp = ""
    for x in st:
        if x == '(':
            temp = temp.replace("\n", "")
            temp = temp.split(" ")
            temp = [x for x in temp if x is not '']
            return ' '.join(temp)
            # return temp
        else:
            temp += x


def course_info_return(dataset, flag):
    course_info = pd.DataFrame()
    t1 = []
    t2 = []
    t3 = []
    t4 = []
    for i, x in enumerate(dataset['Course']):
        t1.append(course_code_return(x))
        t2.append(course_name_return(x))
        t3.append(return_credit(x))
        t4.append(roll_return(dataset['Roll'][i]))
    course_info['course_code'] = t1
    course_info['course_name'] = t2
    course_info['credit'] = t3
    course_info['roll'] = t4
    if flag == 1:
        course_info.to_csv(app.config['SAVE_ROUTINE']+"course_info.csv")
    return course_info


def return_student_info(course_info, flag):
    student_info = pd.DataFrame()
    stu_credit = {}
    stu_course_info = {}
    for x in course_info.values:
        for x2 in x[3].split("|"):
            x2 = int(x2)
            if stu_credit.get(x2) == None:
                stu_credit[x2] = float(x[2])
                stu_course_info[x2] = x[0]
            else:
                stu_credit[x2] += float(x[2])
                stu_course_info[x2] += (","+(x[0]))
    student_info["roll"] = [x for x in stu_course_info]
    student_info['course_code'] = [stu_course_info[x] for x in stu_course_info]
    student_info['credit'] = [stu_credit[x] for x in stu_credit]
    temp = student_info
    temp = temp.sort_values(by=['roll'], ascending=False)
    if flag == 1:
        temp.to_csv(app.config['SAVE_ROUTINE']+"student_info.csv")
    return student_info


def check_lab_starting_point(_df):
    for i, x in enumerate(_df['Course']):
        xx = x.split(" ")[1][:4]
        if int(xx) % 2 == 0:
            return i
    return len(_df)


# merge the same course
overlap = {}


def data_edit(dataset):
    _course = {}
    for i, x in enumerate(dataset['course_code']):
        if x not in _course:
            _course[x] = dataset['roll'][i]
        else:
            overlap[x] = _course[x]+"+"+dataset['roll'][i]
            _course[x] += (sep+(dataset['roll'][i]))
    frq = []
    _leng = []
    __courses = []
    for x in _course:
        __courses.append(x)
        frq.append(_course[x])
        _leng.append(len(_course[x].split(sep)))
    df = pd.DataFrame()
    df["course_code"] = __courses
    df["roll"] = frq
    df["length"] = _leng
    return df
# length wise sort (largest number of students in a course - Descending)


def sorting_data(df):
    final_df = df.sort_values(by=['length'], ascending=False)
    d1 = []
    d2 = []
    d3 = []
    for x in final_df.values:  # for indexing purpose
        d1.append(x[0])
        d2.append(x[1])
        d3.append(x[2])
    data = pd.DataFrame()
    data['course_code'] = d1
    data['roll'] = d2
    data['length'] = d3
    return data


def routine_generate(df, max_student_in_a_day):
    day = 0
    total = 0
    day_assign = []
    exam_taken = 0
    course_assign = []

    def student_check(dat, day_):
        flag = True
        dat = dat.split(sep)
        for x in dat:
            day_roll = str(day_) + "_"+str(x)
            if day_roll in day_assign:
                flag = False
                break
        if flag == True:
            return True
        else:
            return False

    for x in df.length:
        total += x  # number of total student_course instances.
    f = open(app.config['SAVE_ROUTINE']+"exam_routine.csv", 'w')
    dat = "day,course_code,roll\n"
    while(exam_taken != total):
        day += 1
        total_take_in_day = 0  # number of examinee.
        for i, x in enumerate(df['course_code']):
            #print((x not in course_assign))
            if ((total_take_in_day+df['length'][i]) <= max_student_in_a_day) and (x not in course_assign) and student_check(df['roll'][i], day) and not (day == 1 and x[:5] == "EEE 2"):
                for xx in df['roll'][i].split(sep):
                    day_roll = str(day) + "_"+str(xx)
                    day_assign.append(day_roll)
                course_assign.append(df['course_code'][i])
                total_take_in_day += df['length'][i]
                exam_taken += df['length'][i]
                for x2 in df['roll'][i].split(sep):
                    dat += (str(day)+","+str(x)+","+str(x2)+"\n")
    f.write(dat)
    return dat


def overlapping_check(rolls, _course_code, course_info_data):
    val = []
    if len(course_info_data[_course_code].split("+")) == 2:
        da = course_info_data[_course_code].split("+")
        tt = (overlap[_course_code].split("+"))
        str1 = _course_code+"("+str(da[0])+"):"+(','.join(tt[0].split("|")))
        str2 = _course_code+"("+str(da[1])+"):"+(','.join(tt[1].split("|")))
        print(str1)
        print(str2)
        val.append(str1)
        val.append(str2)
    else:
        str1 = _course_code + \
            "("+course_info_data[_course_code]+"):"+(','.join(rolls))
        print(str1)
        val.append(str1)
    return val


def _read_csv(url):
    import pandas as pd
    data = pd.read_csv(url)
    col=data.columns
    print(col)
    if not ('Course' in col and 'Roll' in col):
      return render_template('index.html', result=None, length=0,error="invalid")
    dataset = pd.DataFrame()
    _dataset = pd.DataFrame()
    _dataset['Course'] = data['Course']  # with lab information
    _dataset['Roll'] = data['Roll']  # with lab information
    end = check_lab_starting_point(_dataset)  # check lab starting point
    dataset['Course'] = _dataset['Course'][:end]  # without lab information
    dataset['Roll'] = _dataset['Roll'][:end]  # without lab information
    dataset.index = [x for x in range(0, len(dataset))]
    return dataset, _dataset


@app.route('/download1')
def downloadFile1():
    _path = app.config['SAVE_ROUTINE']+"course_info.csv"
    return send_file(_path, as_attachment=True)


@app.route('/download2')
def downloadFile2():
    _path = app.config['SAVE_ROUTINE']+"routine_backlog.txt"
    return send_file(_path, as_attachment=True)


@app.route('/download3')
def downloadFile3():
    _path = app.config['SAVE_ROUTINE']+"student_info.csv"
    return send_file(_path, as_attachment=True)


@app.route('/download4')
def downloadFile4():
    _path = app.config['SAVE_ROUTINE']+"tutorial.docx"
    return send_file(_path, as_attachment=True)
############################


@app.route('/upload', methods=['GET', 'POST'])
def uploadfile():
    if request.method == 'POST':  
        f = request.files['file']
        student=request.form['student']
        if student=="":
          return render_template('index.html', result=None, length=0,error="empty_student")
        elif (f.filename).split(".")[1]!='csv':
          return render_template('index.html', result=None, length=0,error="invalid_file_format")
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], (f.filename)))
        with open(os.path.join(app.config['UPLOAD_FOLDER'], (f.filename)), newline='') as ff:
          reader = csv.reader(ff)
          row1=""
          for row in reader:
            row1=row
            break
          if not ((row1)[1]=='Course' and (row1)[2]=='Roll'):
            return render_template('index.html', result=None, length=0,error="invalid")
        result, leng = hello_world(f.filename, int(student))
        return render_template('index.html', result=result, length=leng)


@app.route("/", methods=['GET', 'POST'])
def hello_world2():
    return render_template("index.html", result=None, length=0,error=None)


def hello_world(filename,student):
    data = []
    result = []
    if True:
        if True:
            dataset, _dataset = _read_csv(upload_folder+filename)

            course_info_with_lab = course_info_return(_dataset, 1)
            student_info_with_lab = return_student_info(
                course_info_with_lab, 1)
            course_info_data = {}
            for x in course_info_with_lab.values:
                if course_info_data.get(x[0]) == None:
                    course_info_data[x[0]] = x[1]
                else:
                    course_info_data[x[0]] += ("+"+x[1])
            course_info_without_lab = course_info_return(dataset, 0)
            student_info_without_lab = return_student_info(
                course_info_without_lab, 0)
            # dataset=data_clear(dataset)
            dataset = pd.DataFrame()
            dataset['course_code'], dataset['roll'], dataset['length'] = course_info_without_lab['course_code'], course_info_without_lab['roll'], [
                len(x.split("|")) for x in course_info_without_lab['roll']]
            df = data_edit(dataset)
            data = sorting_data(df)
            # course_code,roll(separated by (_)),length
            dat = routine_generate(data, student)
            d1 = []
            d2 = []
            d3 = []
            for i, x in enumerate(dat.split("\n")):
                if i == 0:
                    continue
                xx = x.split(",")
                if len(xx) >= 3:
                    d1.append(xx[0])
                    d2.append(xx[1])
                    d3.append(xx[2])
            df2 = pd.DataFrame()
            df2["day"] = d1
            df2["course_code"] = d2
            df2["roll"] = d3
            import sys
            orig_stdout = sys.stdout
            grouped = df2.groupby(['day', 'course_code'])
            f = open(app.config['SAVE_ROUTINE']+"routine_backlog.txt", 'w')
            sys.stdout = f
            st = ""
            taken = []
            total = 0
            s = set()
            for name, group in grouped:
                if name[0] not in taken:
                    if name[0] != "1":
                        result.append("Total student: "+str(total))
                        print("Total student: ", total)
                        print("Unique student: ", len(s))
                        result.append("Unique student: "+str(len(s)))
                    total = 0
                    s = set()
                    taken.append(name[0])
                    result.append("Day: "+str(name[0]))
                    print("Day: ", name[0], "-"*40)
                rolls = []
                for x in group['roll']:
                    total += 1
                    s.add(x)
                    rolls.append(str(x))
                val = overlapping_check(rolls, name[1], course_info_data)
                result.extend(val)

            print("Total student: ", total)
            result.append("Total student: "+str(total))
            print("Unique student: ", len(s))
            result.append("Unique student: "+str(len(s)))
            sys.stdout = orig_stdout
            f.close()

            return result, int(len(result))

    return render_template('index.html', result=result, length=int(len(result)))


@app.route("/about")
def about():
    return render_template('about.html')


if __name__ == "__main__":
    app.run(debug=True)
