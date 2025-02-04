
import psutil
import subprocess
import re
import platform
import time

class DeviceMonitor:
    def __init__(self,time_delay_s=0.33,log_print=False):
        self.devices = []
        self.time_delay_s=time_delay_s
        self.log_print=log_print
        self.monitor_devices()

    @staticmethod
    def extract_serial(string):
        """Regex search for Serial pattern

        Args:
            string (_type_): text from getserial

        Returns:
            tuple: (id_name, serial_value)
        """
        pattern = r"ID_\w+:\s*(.*?)"
        match = re.search(pattern, string)
        
        if match is None:
            return None
        
        id_name = match.group(1).strip()
        serial_value = match.group(2).strip()
        
        return (id_name, serial_value)

    def get_serial_number_of_physical_disk(self,drive_letter='C:'):
        """Using wmi library for windows, extract Serial Number.
            Note: physical_disk has all info of device
        Args:
            drive_letter (str, optional): Drive letter as windows mounted. Defaults to 'C:'.

        Returns:
            str: Serial Number of device
        """
        # on linux generates error if you import wmi outside. Does not find the dependencies.
        import wmi
        try:
            c = wmi.WMI()
            logical_disk = c.Win32_LogicalDisk(Caption=drive_letter)[0]
            partition = logical_disk.associators()[1]
            physical_disc = partition.associators()[0]
            return physical_disc.SerialNumber
        except Exception as eee:
            print (eee)
            return None

    def get_serial_number(self,device_path):
        """Gets serial numbers in windows and linux for a device.

        Args:
            device_path (str): device

        Returns:
            str: serial number found
        """
        if device_path.startswith('/') and platform.system() == 'Linux':
            # Linux
            disk = next((d for d in psutil.disk_partitions() if device_path == d.device), None)
            if disk:
                # output = subprocess.check_output(['dmidecode', '-s', 'system-uuid', device_path]) # not working
                # return output.decode().strip()
                # udevadm info --query=all --name=/dev/sdc1
                #print(device_path)
                output = subprocess.check_output(['udevadm', 'info', '--query=all', "--name="+device_path]) 
                splitted=str(output.decode()).split("\n")
                endtxt=''
                for txt in splitted:
                    if "SERIAL" in txt:
                        endtxt=endtxt+txt.replace(txt.split(" ",1)[0],"")
                return endtxt #extract_serial(output.decode())
        elif device_path.endswith(':\\') and platform.system() == 'Windows':
            # Windows
            if self.log_print:
                print("Looking for Serial Number in {}".format(device_path.replace('\\','')))
            return self.get_serial_number_of_physical_disk(device_path.replace('\\',''))

        return None

    def monitor_devices(self):
        """Search connected devices and list their serial numbers

        Returns:
            list[list]: list of [device,serial] pairs
        """
        devices=[]
        if platform.system() == 'Darwin':  # macOS
            # macOS (using iokit)
            # Not tested! could be ioreg -lp IOUSB, ioreg -l
            import io
            output = subprocess.check_output(['ioctl', '-k', '/dev/disk0', 'iomgr'])
            devices=list(output.decode().strip())
        else:
            # Linux
            # Windows
            for disk in psutil.disk_partitions():
                serials=self.get_serial_number(disk.device)
                #print(f"Using {disk.device} psutil: {serials}")
                time.sleep(self.time_delay_s) #windows is slow to query. If asked too fast responds unknown
                devices.append([disk.device,serials])
        self.devices=devices
        return devices
    
    def check_none_devices(self):
        """Search again no serial devices which are connected devices and list their serial numbers
           Sometimes the windows api does not respond correctly. You can recheck as many times you want.
           
        Returns:
            list[list]: list of [device,serial] pairs
        """
        devices=[]
        for device,serial in self.devices:
            if serial:
                devices.append([device,serial])
            else:

                if platform.system() == 'Darwin':  # macOS
                    print("Not implemented :( !!!")
                else:
                    # Linux
                    # Windows
                    time.sleep(self.time_delay_s) #windows is slow to query. If asked too fast responds unknown
                    serial_2=self.get_serial_number(device)  
                    devices.append([device,serial_2])
                self.devices=devices
        return devices

if __name__ == '__main__':
    md=DeviceMonitor(log_print=True)
    for _,serial in md.devices:
        if not serial:
            md.check_none_devices()

    print(md.devices)
