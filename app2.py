from flask import Flask, render_template, request, redirect
from datetime import datetime
from collections import Counter
import matplotlib
import uuid
import matplotlib.pyplot as plt
import io
import base64
import json
import re

matplotlib.use('Agg') 

app = Flask(__name__)

# using imported re(regular expression) module to check if inputed value contains only letters(upper or lower case).
def is_validated(inputed_value):
    pattern = r'^([A-Za-z]+$)' # ^ and $ ensure inputed value are checked from beginiing to the end respectively.
    formatted_data = ''.join(inputed_value.split()) # split data before checking and join after checking.
    if re.match(pattern, formatted_data):
        return True



tasks_filename = "user_tasks.json"
try:   
    with open(tasks_filename, "r") as file:
        tasks = json.load(file)
except FileNotFoundError:
    tasks = []


completed_tasks_filename = "completed_tasks.json"
try:
    with open(completed_tasks_filename, mode = "r") as file:
        completed_tasks = json.load(file)
except FileNotFoundError:
    completed_tasks = []



@app.route('/')
def index():
    priority_mapping = {'High': 1, 'Medium': 2, 'Low': 3}
    sorted_tasks = sorted(tasks, key=lambda x: priority_mapping.get(x.get('priority', 'Low')))
    return render_template('index.html', tasks=sorted_tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    new_task = request.form.get('task')
    priority = request.form.get('priority')
    category = request.form.get('category')

    # call the function is_validated to validate data and return appropriate message
    if  not is_validated(new_task):
        message = 'Enter a valid task'
        return render_template('index.html', message = message,  tasks = tasks)
    
    if new_task:
        # generate an id using a unique id generator
        task_id = str(uuid.uuid4())
        #inserting new task to indent zero so it becomes the first item in the list
        tasks.insert(0,{
            'id': task_id , 
            'task': new_task, 
            'completed': False, 
            'priority': priority,  # Save the priority from the form
            'category': category   # Save the category from the form
        })
        #writing the new list of tasks to the tasks.json file
        with open(tasks_filename, "w") as file:
            json.dump(tasks, file, default=str, indent= 4)   # Use default=str to serialize datetime objects
  
    return redirect('/')


@app.route('/complete/<task_id>')
def complete_task(task_id):
    global tasks, completed_tasks
    task_found = False
    
    # Find the task with the given task_id
    for task in tasks:
        if task['id'] == task_id and not task['completed']:
            # Mark the task as completed
            task['completed'] = True
            task["completion_time"] = datetime.now()  # Saving the datetime object
            task_found = True
            break  # Exit the loop after completing the task

    # Save tasks to the JSON file only if a task was found and completed
    if task_found:
        with open(tasks_filename, mode = "w") as file:
            json.dump(tasks, file, default=str, indent= 4)   # Use default=str to serialize datetime objects

    completed_tasks.insert(0,task)

    completed_tasks_filename = "completed_tasks.json"           
    with open(completed_tasks_filename, mode = "w") as file:
        json.dump(completed_tasks, file, default=str, indent= 4) # Use default=str to serialize datetime objects
    return redirect('/')



@app.route('/delete/<task_id>')
def delete_task(task_id):
    global tasks
    for task in tasks:
        if task['id'] == task_id:
            tasks.remove(task)
            break
    #removing the deleted task from the file and rewriting new list of task to the tasks.json file
    with open(tasks_filename, "w") as file:
        json.dump(tasks, file, default=str, indent= 4)   # Use default=str to serialize datetime objects 
           
    return redirect("/")
    
    # ... (TO-DO: Complete the code...)


@app.route('/insights')
def insights():
    global tasks

    completed_tasks = []
    completed_tasks_filename = "completed_tasks.json"
    try:
        with open(completed_tasks_filename, mode = "r") as file:
            completed_tasks = json.load(file)
            for task_data in completed_tasks:
                #convert the completion_time string back to a datetime object
                datetime_format = "%Y-%m-%d %H:%M:%S.%f"
                if "completion_time" in task_data:
                    task_data["completion_time"] = datetime.strptime(task_data["completion_time"], datetime_format)
    except FileNotFoundError:
        pass

    
    # Getting the recent completed tasks based on the week number    
    recent_completed_tasks = [task for task in completed_tasks if task["completion_time"].strftime("%W") == completed_tasks[0]["completion_time"].strftime("%W")]
    

    # Calculate completion counts by day
    completion_counts = Counter(time.date() for task in completed_tasks for key, time in task.items() if key == "completion_time")

    # Calculate completion counts by day based on the week number
    completed_counts = Counter(time.strftime("%A") for task in recent_completed_tasks for key, time in task.items() if key == "completion_time")

    # Generate a pie chart for completed tasks
    labels = completed_counts.keys()
    values = completed_counts.values()


    plt.figure(figsize=(10, 6))
    plt.pie(values, autopct= "%.1f%%", startangle= 90, textprops = dict(color = "w"))
    plt.title('Completed Tasks')
    plt.legend(labels, title = "Days of Completed Tasks", loc = "best", bbox_to_anchor = (1,0,0.5,1)) 
    # bbox_to_anchor argument used to position the legend outside of the pie.

    
    # Save the plot to a base64 encoded image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.read()).decode()
    date = datetime.now().date()

    return render_template('insights.html', chart_base64=plot_url, completion_counts = completion_counts)
    


if __name__ == '__main__':
    app.run( debug=True, port=5002)


