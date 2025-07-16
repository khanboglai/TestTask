import psutil


class ProcessManager:
    def __init__(self, pid_list):
        self.pid_list = pid_list

    
    def check_isalive(self, pid):
        try:
            psutil.Process(pid)
            return True
        except psutil.NoSuchProcess:
            return False
        
    def update(self):
        self.pid_list = [pid for pid in self.pid_list if self.check_isalive(pid)]
        
    

# data = ProcessManager([10856])

# print(data.check_isalive(7956))