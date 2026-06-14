# Kali VM Network Diagnostics — Session Checklist

Reproduced from a real session where Kali was running but SSH was unreachable.

## Phase 1 — Verify VM State

```bash
VBoxManage list runningvms
# Expected: "kal" UUID
VBoxManage showvminfo "kal" --machinereadable | grep VMState=
# Expected: "running" — if not, start the VM
```

## Phase 2 — Network Interface Inspection

```bash
VBoxManage showvminfo "kal" --machinereadable | grep -E "^(nic|macaddress)" | head -20
```

Check:
- nic1 type (hostonly / nat / bridged)
- Has MAC address for each NIC
- Has a second NIC (bridged) if needed

## Phase 3 — Host-Only Network Scan

```bash
nmap -sn 192.168.56.0/24
# Look for 192.168.0.19 or any host with VirtualBox MAC (08:00:27:*)
```

If Kali's IP is not present → network stack is broken inside Kali.

## Phase 4 — GuestInfo Check

```bash
VBoxManage guestproperty get "kal" "/VirtualBox/GuestInfo/Net/0/V4/IP"
# "No value set!" = Guest Additions not installed or not running
```

## Phase 5 — Bridged Network Scan (if bridged NIC exists)

```bash
# Find own WiFi subnet first
ip addr show | grep "inet " | grep -v 127.0.0.1
# Then scan for Kali's bridged MAC
nmap -sn 192.168.0.0/24
```

Kali's MAC prefix: `08:00:27:BC:0E:BA` (bridged) or `08:00:27:E2:02:51` (host-only / internal)

## Phase 6 — Root Cause

If all above show the VM as running but no IP is reachable on any interface:
→ **`/etc/network/interfaces` has a `auto eth0` line that breaks NetworkManager.**

Fix: boot VM via VirtualBox GUI, or use recovery VM with NAT + port forwarding, then:

```bash
sudo systemctl mask networking
sudo systemctl unmask NetworkManager
sudo systemctl enable --now NetworkManager
sudo dhclient eth0
```

## Phase 7 — Verify Connectivity

```bash
# From Windows
sshpass -p 'kali' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 kali@192.168.0.19 "ip addr show | grep inet"
```

## Recovery VM Creation Recipe

If GUI access is impossible:

```bash
# Clone VDI path from original VM
VBoxManage showvminfo "kal" | grep "SATA" | grep "vdi"

# Create recovery VM with NAT + SSH port forwarding
VBoxManage createvm --name "kal-recovery" --ostype Debian_64 --register
VBoxManage modifyvm "kal-recovery" --memory 2048 --acpi on --boot1 dvd
VBoxManage modifyvm "kal-recovery" --nic1 nat --natpf1 "ssh,tcp,,2224,,22"
VBoxManage storagectl "kal-recovery" --name "IDE" --add ide --controller PIIX4
VBoxManage storageattach "kal-recovery" --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium "C:\path\to\systemrescue.iso"
VBoxManage storageattach "kal-recovery" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "C:\path\to\kali.vdi"

# Start
VBoxManage startvm "kal-recovery"

# Wait for boot, then SSH
sshpass -p 'recovery' ssh -p 2224 -o StrictHostKeyChecking=no root@127.0.0.1 "bash"

# Mount Kali root
fdisk -l | grep "Linux"
mount /dev/sda2 /mnt  # adjust partition number
chroot /mnt /bin/bash
# Now run the fix commands
```

## Phase 8 — Verification

After fix, from Windows:
```bash
# Kill recovery VM first
VBoxManage controlvm "kal-recovery" poweroff
sleep 3
VBoxManage list runningvms  # should be empty

# Start original Kali
VBoxManage startvm "kal" --type headless
sleep 15

# Test SSH
sshpass -p 'kali' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 kali@192.168.0.19 "whoami"
```
