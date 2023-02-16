from support import *


# We can user LinuxConnection, really paramiko to make a connection to windows server as well but we will use winrem for diversity

report_portal_path = r"D:\Python Projects\report_portal\Scripts\Portal"
linux_portal_path = r"/home/ahmed/Desktop/AHMED/Django_Websites/reports_portal/Portal"
window_portal_path = r"C:\AhmedWebsites\report_portal\Scripts\Portal"


################################################################
# Linux Server Connnection
################################################################

linconn = RemoteConnection(
    ip="172.20.100.81", username="ahmed", password="ahmed", os_type="linux"
)


linconn.copy_files_to_server(
    report_portal_path,
    linux_portal_path,
)

linconn.run_ssh_command_on_server(
    f" cd Desktop;cd AHMED;cd Django_Websites;cd reports_portal;cd Portal; echo 'ahmed' |  sudo  -S chmod -R 777 *;cd web_excel_files;ls; rm -rf *",
    remote_entry_path=None,
    type=1,
)

linconn.linux_restart_services()

linconn.close_connection()

################################################################
# Windows Server Connnection
################################################################

winconn = RemoteConnection(
    "172.20.200.40", "itapps@KDAHIT", "Kh@123457", os_type="windows"
)

winconn.copy_files_to_server(
    report_portal_path,
    window_portal_path,
)

winconn.run_ssh_command_on_server(
    f"cd {window_portal_path} && dir",
    remote_entry_path=None,
    type=1,
)



winconn.close_connection()


# sup.report_portal_publish_windows(
#     report_portal_path,
#     r"\\172.20.200.40\c$\AhmedWebsites\report_portal\Scripts\Portal",
# )
