
import psutil
import subprocess
import platform
import time



class DeviceMonitor:
    def __init__(self,time_delay_s=0.33,log_print=False):
        self.devices = []
        self.time_delay_s=time_delay_s
        self.log_print=log_print
        self.monitor_devices()


    @staticmethod
    def linux_disk_drive_to_dict(text:str):
        """Set udevadm info --query=all --name=/dev/... information response in a dictionary.

        Args:
            text (str): Output from udevadm info query

        Returns:
            dict: dictionary with information
        """
        splitted=text.split("\n")
        # Initialize an empty dictionary to store the result
        disk_drive_info = {}
        for txt in splitted:
            if 'E: ' in txt:
                rem_e_list=txt.replace('E: ','').split('=')
                disk_drive_info.update({rem_e_list[0]:rem_e_list[1]})
        return disk_drive_info 

    @staticmethod
    def win32_disk_drive_to_dict(instance):
        """
        Converts a Win32_DiskDrive instance to a dictionary.
        
        Args:
            instance (object): The Win32_DiskDrive instance as an object.

        Returns:
            dict: A dictionary representation of the Win32_DiskDrive instance with all keys.
        """

        # Define the properties and their corresponding keys in a dictionary
        property_map = {
            "BytesPerSector": "bytes_per_sector",
            "Capabilities": "capabilities",
            "CapabilityDescriptions": "capability_descriptions",
            "Caption": "caption",
            "ConfigManagerErrorCode": "config_manager_error_code",
            "ConfigManagerUserConfig": "config_manager_user_config",
            "CreationClassName": "creation_class_name",
            "Description": "description",
            "DeviceID": "device_id",
            "FirmwareRevision": "firmware_revision",
            "Index": "index",
            "InterfaceType": "interface_type",
            "Manufacturer": "manufacturer",
            "MediaLoaded": "media_loaded",
            "MediaType": "media_type",
            "Model": "model",
            "Name": "name",
            "Partitions": "partitions",
            "PNPDeviceID": "pnp_device_id",
            "SCSIBus": "scsi_bus",
            "SCSILogicalUnit": "scsi_logical_unit",
            "SCSIPort": "scsip_port",
            "SCSITargetId": "scsit_target_id",
            "SectorsPerTrack": "sectors_per_track",
            "SerialNumber": "serial_number",
            "Size": "size",
            "Status": "status",
            "SystemCreationClassName": "system_creation_class_name",
            "SystemName": "system_name",
            "TotalCylinders": "total_cylinders",
            "TotalHeads": "total_heads",
            "TotalSectors": "total_sectors",
            "TotalTracks": "total_tracks",
            "TracksPerCylinder": "tracks_per_cylinder"
        }
        # Initialize an empty dictionary to store the result
        disk_drive_info = {}

        # Iterate over the properties and add them to the dictionary
        for prop, key in property_map.items():
            if hasattr(instance, prop):
                value = getattr(instance, prop)
                if isinstance(value, (tuple, list)):
                    disk_drive_info[key] = ', '.join(map(str, value))
                else:
                    disk_drive_info[key] = str(value)

        return disk_drive_info

    def get_serial_number_of_physical_disk(self,drive_letter='C:'):
        """Using wmi library for windows, extract Serial Number.
            Note: physical_disk has all info of device
        Args:
            drive_letter (str, optional): Drive letter as windows mounted. Defaults to 'C:'.

        Returns:
            str: Serial Number of device
        """
        # on linux generates error if you import wmi outside. Does not find the dependencies.
        if platform.system() == 'Windows':
            import wmi
            try:
                c = wmi.WMI()
                logical_disk = c.Win32_LogicalDisk(Caption=drive_letter)[0]
                partition = logical_disk.associators()[1]
                
                physical_disc = partition.associators()[0]
                try:
                    a_serial=physical_disc.properties['SerialNumber']
                    if a_serial:
                        return a_serial
                except:
                    pass
                try:
                    a_serial=physical_disc.SerialNumber
                except:
                    return None
                return a_serial
            except Exception as eee:
                print (eee)
        return None
    
    def get_info_windows_device(self,drive_letter='C:'):
        """Using wmi library for windows, extract Serial Number.
            Note: physical_disk has all info of device
        Args:
            drive_letter (str, optional): Drive letter as windows mounted. Defaults to 'C:'.

        Returns:
            str: Serial Number of device
        """
        # on linux generates error if you import wmi outside. Does not find the dependencies.
        if platform.system() == 'Windows':
            import wmi
            try:
                c = wmi.WMI()
                logical_disk = c.Win32_LogicalDisk(Caption=drive_letter)[0]
                partition = logical_disk.associators()[1]
                physical_disc = partition.associators()[0]
                return self.win32_disk_drive_to_dict(physical_disc)
            except Exception as eee:
                print (eee)
                return None
        return None
    
    
    def get_info_linux_device(self,device_path="/dev/sda"):
        """Using udevadm info --query=all --name=/dev/... , extract all info.
            Note: physical_disk has all info of device
        Args:
            device_path (str, optional): Drive letter as windows mounted. Defaults to '/dev/sda'.

        Returns:
            str: Serial Number of device
        """
        if device_path.startswith('/') and platform.system() == 'Linux':
            # Linux
            disk = next((d for d in psutil.disk_partitions() if device_path == d.device), None)
            if disk:
                output = subprocess.check_output(['udevadm', 'info', '--query=all', "--name="+device_path]) 
                return self.linux_disk_drive_to_dict(str(output.decode()))

    def get_serial_number(self,device_path):
        """Gets serial numbers in windows and linux for a device.

        Args:
            device_path (str): device

        Returns:
            str: serial number found
        """
        if device_path.startswith('/') and platform.system() == 'Linux':
            # Linux
            info_dict=self.get_info_linux_device(device_path)
            endtxt=''
            iii=0
            sep=''
            for key,value in info_dict.items():
                if 'SERIAL' in key:
                    if key == 'ID_SERIAL_SHORT':
                        return value   
                    if iii>0:
                        sep='|'
                    endtxt=endtxt+sep+value
                    iii=iii+1
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
                if platform.system() == 'Windows':
                    devices.append([disk.device,serials])
                elif platform.system() == 'Linux':
                    devices.append([disk.mountpoint,serials])
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
    device_mount=md.devices[len(md.devices)-1][0]
    if platform.system() == 'Windows':
        info=md.get_info_windows_device(device_mount.replace('\\',''))
        print(f'Windows Information on {device_mount}')
        print("info:\n",info)
        print("type:\n",type(info))
    if platform.system() == 'Linux':
        info=md.get_info_linux_device(device_mount)        
        print(f'Linux Information on {device_mount}')
        print("info:\n",info)
        print("type:\n",type(info))

