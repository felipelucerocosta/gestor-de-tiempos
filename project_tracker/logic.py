from datetime import datetime, timedelta
import math

def calculate_stages(start_date_str, end_date_str):
    """Divides the time between start and end date into 5 equal stages."""
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    total_days = (end_date - start_date).days
    if total_days <= 0:
        return []
    
    stage_duration = total_days / 5
    stages = []
    for i in range(1, 6):
        stage_date = start_date + timedelta(days=math.ceil(stage_duration * i))
        stages.append({
            "name": f"Etapa {i}",
            "due_date": stage_date.strftime("%Y-%m-%d")
        })
    return stages

def process_graph_data(logs, tasks, start_date_str, end_date_str):
    """
    Processes logs and tasks into data suitable for a Matplotlib graph.
    Returns: dates (list), cumulative_progress (list)
    """
    # Combine logs and tasks into events
    events = []
    for log in logs:
        # log: (id, project_id, timestamp, description, progress_score)
        events.append({
            "date": datetime.strptime(log[2], "%Y-%m-%d %H:%M:%S"),
            "score": log[4],
            "type": "log"
        })
    
    # Task completion bonus (arbitrary logic: added at the moment it's processed or spread?)
    # For simplicity, if we don't have task completion timestamps, we can't plot them accurately over time.
    # Let's assume for now tasks are just bonus points added to the total.
    # OR: If we want them in the graph, we'd need timestamps for task completion.
    # Let's add a 'bonus' from tasks to the final point for now, or imagine they were done.
    
    if not events:
        return [], []
        
    events = sorted(events, key=lambda x: x['date'])
    
    dates = []
    progress_values = []
    current_total = 0
    
    # Start point
    start_date = datetime.strptime(start_date_str.split()[0], "%Y-%m-%d")
    dates.append(start_date)
    progress_values.append(0)
    
    last_date = start_date
    
    for event in events:
        event_date = event['date']
        
        # Decay logic
        days_gap = (event_date - last_date).days
        if days_gap > 1:
            current_total -= (days_gap - 1) * 0.5
            if current_total < 0: current_total = 0
            
        current_total += event['score']
        dates.append(event_date)
        progress_values.append(current_total)
        last_date = event_date

    # Add Task Bonus at the end
    completed_tasks = [t for t in tasks if t[3] == 1]
    task_bonus = len(completed_tasks) * 2 # +2 points per task
    if dates:
        progress_values[-1] += task_bonus
        
    return dates, progress_values
