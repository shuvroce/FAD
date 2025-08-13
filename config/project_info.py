from datetime import date

class ProjectInfo():
    def __init__(self, project_name, rev_no, date_time):
        self.project_name = project_name
        self.rev_no = rev_no
        self.date_time = date_time
    
    def get_project_info(self):
        project_info = {
            "project_name": self.project_name,
            "rev_no": self.rev_no,
            "date_time": self.date.today().strftime("%d/%m/%Y")
        }
        return project_info
