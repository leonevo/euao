import paramiko
class EUAOSSHClient(paramiko.SSHClient):
## overload the exec_command method 
    def exec_command(self, command, bufsize=-1, timeout=None): 
        chan = self._transport.open_session() 
        chan.settimeout(timeout) 
        chan.exec_command(command) 
        stdin = chan.makefile('wb', bufsize) 
        stdout = chan.makefile('rb', bufsize) 
        stderr = chan.makefile_stderr('rb', bufsize) 
        return stdin, stdout, stderr
    
if __name__ == '__main__':
    cmd=r'mksyscfg -r lpar -m Server-9117-MMA-SN06D6D82 -i "name=testEUAOclient,profile_name=default,lpar_env=aixlinux,min_mem=1024,desired_mem=2048,max_mem=32768,proc_mode=shared,min_procs=1,desired_procs=2,max_procs=16,min_proc_units=0.1,desired_proc_units=0.5,max_proc_units=16,sharing_mode=uncap,uncap_weight=128,auto_start=1,boot_mode=norm,max_virtual_slots=1000,\"virtual_eth_adapters=22/0/1///1,23/0/2///1\",\"virtual_scsi_adapters=20/client//VIOserver1/23/1,21/client//VIOserver2/23/1\""'
    #ExecuteSimpleCMDviaSSH2('182.247.251.247','hscroot','abc1234',cmd)
    #ExecuteCMDviaSSH2('182.247.251.247','hscroot','abc1234',cmd,connect_timeout=5,command_timeout=20,cmd_prompt='hscroot@localhost:~>')
    sc=EUAOSSHClient()    