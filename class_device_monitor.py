
import psutil
import subprocess
import platform
import time
import threading

if platform.system() == 'Windows':
    # Initialize COM
    import pythoncom
    import wmi
elif platform.system() == 'Darwin':
    import io


class TimeoutException(Exception): pass

class TimerThread(threading.Thread):
    def __init__(self, target, timeout_seconds=10):
        super().__init__()
        self.target = target
        self.timeout_seconds = timeout_seconds

    def run(self):
        start_time = time.time()
        while True:
            try:
                result = self.target()
                if isinstance(result, Exception):  # If an exception was raised in the target function
                    raise result
                return result
            except (KeyboardInterrupt, SystemExit):
                raise
            finally:
                elapsed_time = time.time() - start_time
                if elapsed_time > self.timeout_seconds:
                    print(f"Timeout after {self.timeout_seconds} seconds")
                    return 'Timeout'


class DeviceMonitor:
    def __init__(self,time_delay_s=0.33,log_print=False):
        self.devices = []
        self.time_delay_s=time_delay_s
        self.log_print=log_print
        self.timer_thread=None

    def refresh(self, log_print=None):
        """Refresh the list of connected devices."""

        if log_print is not None:
            self.log_print = log_print

        self.devices.clear()
        self.monitor_devices()
    
    def find_mount_serial_of_path(self, path: str):
        """Return the mount point and serial for the device containing ``path``.

        Args:
            path (str):
                Path to locate.

        Returns:
            tuple:
                ``(mount, serial)`` if found, otherwise ``("", "")``.
        """
        mount = ""
        serial = ""
        longest_match = -1

        if not isinstance(self.active_devices, list):
            return mount, serial

        for device_mount, device_serial in self.active_devices:

            if platform.system() == 'Windows':
                # Windows does not consistently report drive letters with the same case
                # (e.g. "C:" vs "c:"). Compare case-insensitively to avoid treating the
                # same device as disconnected.
                if (
                    path.startswith(device_mount)
                    or path.startswith(device_mount.lower())
                    or path.startswith(device_mount.upper())
                ):
                    mount = device_mount
                    serial = device_serial
                    break

            else:
                if (
                    path.startswith(device_mount)
                    and len(device_mount) > longest_match
                ):
                    longest_match = len(device_mount)
                    mount = device_mount
                    serial = device_serial

        return mount, serial

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

    def _get_serial_number_of_physical_disk(self,drive_letter='C:'):
        """Using wmi library for windows, extract Serial Number.
            Note: physical_disk has all info of device
        Args:
            drive_letter (str, optional): Drive letter as windows mounted. Defaults to 'C:'.

        Returns:
            str: Serial Number of device
        """
        # on linux generates error if you import wmi outside. Does not find the dependencies.
        if platform.system() == 'Windows':
            # import wmi
            try:
                pythoncom.CoInitialize()
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
    
    def _get_info_windows_device(self,drive_letter='C:'):
        """Using wmi library for windows, extract Serial Number.
            Note: physical_disk has all info of device
        Args:
            drive_letter (str, optional): Drive letter as windows mounted. Defaults to 'C:'.

        Returns:
            str: Serial Number of device
        """
        # on linux generates error if you import wmi outside. Does not find the dependencies.
        if platform.system() == 'Windows':
            # import wmi
            try:
                pythoncom.CoInitialize()
                c = wmi.WMI()
                logical_disk = c.Win32_LogicalDisk(Caption=drive_letter)[0]
                partition = logical_disk.associators()[1]
                physical_disc = partition.associators()[0]
                return self.win32_disk_drive_to_dict(physical_disc)
            except Exception as eee:
                print (eee)
                return None
        return None
    
    def _mount_to_device_macos(self, mount_point):
        """
        Returns the device mounted at a macOS mount point.

        Args:
            mount_point (str): Volume mount path.

        Returns:
            str | None: Device identifier (/dev/diskXsY)
        """

        try:
            output = subprocess.check_output(
                [
                    "df",
                    mount_point
                ],
                text=True
            )

            lines = output.strip().splitlines()

            if len(lines) > 1:
                device = lines[1].split()[0]
                return device

        except subprocess.CalledProcessError:
            pass

        return None
    
    def _get_info_macos_device(self, device_or_mount):
        """
        Gets macOS disk information.

        Accepts either:
            /dev/disk4s1
            /Volumes/MyDrive

        Returns:
            dict | None
        """

        if platform.system() != "Darwin":
            return None

        if device_or_mount.startswith("/Volumes"):
            device = self._mount_to_device_macos(device_or_mount)
        else:
            device = device_or_mount

        if not device:
            return None

        try:
            output = subprocess.check_output(
                [
                    "diskutil",
                    "info",
                    device
                ],
                text=True
            )

            return self.macos_diskutil_to_dict(output)

        except subprocess.CalledProcessError:
            return None
        
    @staticmethod
    def macos_diskutil_to_dict(text: str):
        """
        Converts diskutil info output into a dictionary.

        Args:
            text (str): Output from diskutil info.

        Returns:
            dict: Dictionary containing disk information.
        """

        disk_drive_info = {}
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)

            key = key.strip()
            value = value.strip()

            if key and value:
                disk_drive_info[key] = value

        return disk_drive_info

    def _mount_to_device(self, mount_point):
        """
        Returns the Linux block device mounted at a given path.

        Args:
            mount_point (str): Mounted filesystem path.

        Returns:
            str | None: Device path such as /dev/sdb1.
        """
        for partition in psutil.disk_partitions(all=False):

            if not self._is_real_linux_device(partition):
                continue

            if partition.mountpoint == mount_point:
                return partition.device

        return None
    
    def get_device_info(self, device_path):
        """
        Gets device information using the platform-specific backend.

        Args:
            device_path (str):
                Device path, mount point, or platform identifier.

        Returns:
            dict | None:
                Dictionary containing available device information.
        """

        system = platform.system()

        if system == "Linux":
            return self._get_info_linux_device(device_path)

        elif system == "Windows":
            return self._get_info_windows_device(device_path)

        elif system == "Darwin":
            return self._get_info_macos_device(device_path)

        return None
    
    def _get_info_linux_device(self, device_or_mount="/dev/sda"):
        """
        Gets udev information for a Linux block device.

        Args:
            device_or_mount (str): Block device path (/dev/sda1).

        Returns:
            dict: Device information.
        """

        if not device_or_mount.startswith("/") or  platform.system() != 'Linux':
            return None
        #disk = next((d for d in psutil.disk_partitions(all=True) if device_or_mount == d.device), None)
        disk = next((d for d in psutil.disk_partitions() if device_or_mount == d.device), None)
        if disk is None:
            dev_path = self._mount_to_device(device_or_mount)
        else:
            dev_path = device_or_mount
        
        if dev_path is None:
                return None

        try:
            output = subprocess.check_output(
                [
                    "udevadm",
                    "info",
                    "--query=all",
                    "--name=" + dev_path
                ],
                text=True
            )

            return self.linux_disk_drive_to_dict(output)

        except subprocess.CalledProcessError:
            return None
    
    def _is_real_linux_device(self, partition):
        """
        Returns True if a mounted partition represents a physical device.
        """

        device = partition.device

        # Ignore virtual filesystems
        if not device.startswith("/dev/"):
            return False

        # Ignore loop devices (snap, app images, etc.)
        if "/loop" in device:
            return False

        # Ignore ram devices
        if device.startswith("/dev/ram"):
            return False

        return True

    def get_serial_number(self, device_path):
        """
        Gets the device serial identifier for the current platform.

        Args:
            device_path (str):
                Device path, mount point, or platform-specific identifier.

        Returns:
            str | None:
                Serial identifier if available.
        """
        system = platform.system()

        if system == "Linux":
            info_dict = self._get_info_linux_device(device_path)

            if not info_dict:
                return None

            serials = []

            for key, value in info_dict.items():
                if "SERIAL" in key:
                    if key == "ID_SERIAL_SHORT":
                        return value

                    serials.append(value)

            return "|".join(serials)

        elif system == "Windows":
            if device_path.endswith(":\\"):
                path=device_path.replace('\\','')
                if self.log_print:
                    print(f"Looking for Serial Number in {path}")
                return self._get_serial_number_of_physical_disk(path)

        elif system == "Darwin":
            info_dict = self._get_info_macos_device(device_path)

            if not info_dict:
                return None

            # diskutil uses this naming
            for key in (
                "Serial Number",
                "Device Serial Number",
                "Disk / Partition UUID",
                "Volume UUID",
            ):
                if key in info_dict:
                    return info_dict[key]

        return None

    def monitor_devices(self):
        # Create a timer thread to call get_devices function with 10-second timeout
        self.timer_thread = TimerThread(self._monitor_devices, timeout_seconds=33)
        result = None
    
        try:
            self.timer_thread.start()
            if not self.timer_thread.is_alive(): 
                print("Operation timed out")
                return self.devices
            
            # Wait for the thread to finish and get its return value
            result = self.timer_thread.join(timeout=10)  # Wait for up to 5 seconds before giving up
            
        except TimeoutException:
            print("Operation timed out")
            return 'Timeout'

        if isinstance(result, Exception): 
            print(f"Error: {result}")
        
        # else:
        #     print(result)
        #     # devices = result
        return result
            

    def _monitor_devices(self):
        """
        Searches connected storage devices and stores mount point and identifier.

        Returns:
            list[list]:
                List of [mount_point, serial] pairs.
        """
        devices = []
        try:
            system = platform.system()
            for disk in psutil.disk_partitions():
                # Skip virtual filesystems
                if not self._is_valid_device(disk):
                    continue
                serial = self.get_serial_number(disk.device)

                # Windows can require delay between queries
                if system == "Windows":
                    time.sleep(self.time_delay_s)

                if system == "Windows":
                    mount = disk.device

                elif system in ("Linux", "Darwin"):
                    mount = disk.mountpoint

                else:
                    continue

                devices.append(
                    [
                        mount,
                        str(serial) if serial else ""
                    ]
                )

            self.devices = devices

        except Exception as e:
            print(f"[red] Error monitoring device: {e}")

        return self.devices
    
    def _is_valid_device(self, disk):
        """
        Returns True if the partition belongs to a physical storage device.
        """

        system = platform.system()

        if system == "Linux":
            # must originate from a block device
            if not disk.device.startswith("/dev/"):
                return False
            # ignore virtual loop devices
            if disk.device.startswith("/dev/loop"):
                return False
            # ignore RAM devices
            if disk.device.startswith("/dev/ram"):
                return False
            # ignore compressed RAM
            if disk.device.startswith("/dev/zram"):
                return False
            return True
        
        elif system == "Windows":
            # keep all drive letters
            return disk.device.endswith(":\\")

        elif system == "Darwin":
            # keep real disk partitions
            return disk.device.startswith("/dev/disk")

        return False
    
    def check_none_devices(self):
        """Search again no serial devices which are connected devices and list their serial numbers
           Sometimes the windows api does not respond correctly. You can recheck as many times you want.

        Returns:
            list[list]: list of [device,serial] pairs
        """
        devices=[]
        for device,serial in self.devices:
            if serial:
                devices.append([device,str(serial)])
            else:
                try:
                    if platform.system() == 'Darwin':  # macOS
                        print("Not implemented :( !!!")
                    else:
                        # Linux
                        # Windows
                        time.sleep(self.time_delay_s) #windows is slow to query. If asked too fast responds unknown
                        serial_2=self.get_serial_number(device)  
                        devices.append([device,str(serial_2)])
                except Exception as eee:
                    print(f"Device {device} serial unavailable: {eee}")
                self.devices=devices
        return devices

if __name__ == '__main__':
    md=DeviceMonitor(log_print=True)
    md.monitor_devices()
    for _,serial in md.devices:
        if not serial:
            md.check_none_devices()

    print(md.devices)
    device_mount=md.devices[len(md.devices)-1][0]
    if platform.system() == 'Windows':
        info=md._get_info_windows_device(device_mount.replace('\\',''))
        print(f'Windows Information on {device_mount}')
        print("info:\n",info)
        print("type:\n",type(info))
    if platform.system() == 'Linux':
        info=md._get_info_linux_device(device_mount)        
        print(f'Linux Information on {device_mount}')
        print("info:\n",info)
        print("type:\n",type(info))

