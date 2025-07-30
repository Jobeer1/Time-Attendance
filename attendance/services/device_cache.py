"""
Device Cache Manager for Network Discovery
Manages device cache in JSON format with persistent storage
"""

import json
import os
import threading
import ipaddress
from datetime import datetime
from typing import Dict, Optional, List, Any
import logging

class DeviceCacheManager:
    """Manages device cache stored in JSON format"""
    
    def __init__(self, cache_file_path: str):
        self.cache_file_path = cache_file_path
        self.cache_data = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
        
        # Load existing cache
        self.load_cache()
    
    def load_cache(self) -> bool:
        """Load device cache from JSON file"""
        try:
            with self.lock:
                if os.path.exists(self.cache_file_path):
                    with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                        self.cache_data = json.load(f)
                    self.logger.info(f"Loaded device cache from {self.cache_file_path}")
                    return True
                else:
                    # Create initial cache structure
                    self.cache_data = {
                        "networks": {},
                        "metadata": {
                            "version": "1.0",
                            "last_updated": datetime.now().isoformat(),
                            "total_devices": 0,
                            "total_networks": 0
                        }
                    }
                    self.save_cache()
                    return True
        except Exception as e:
            self.logger.error(f"Error loading device cache: {e}")
            return False
    
    def save_cache(self) -> bool:
        """Save device cache to JSON file"""
        try:
            with self.lock:
                # Update metadata
                self.cache_data["metadata"]["last_updated"] = datetime.now().isoformat()
                self.cache_data["metadata"]["total_networks"] = len(self.cache_data.get("networks", {}))
                
                # Count total devices
                total_devices = 0
                for network_data in self.cache_data.get("networks", {}).values():
                    total_devices += len(network_data.get("devices", {}))
                self.cache_data["metadata"]["total_devices"] = total_devices
                
                # Save to file with pretty formatting
                with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Saved device cache to {self.cache_file_path}")
                return True
        except Exception as e:
            self.logger.error(f"Error saving device cache: {e}")
            return False
    
    def get_network_key(self, ip_address: str) -> Optional[str]:
        """Get network key for an IP address"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check existing networks
            for network_key in self.cache_data.get("networks", {}):
                try:
                    network = ipaddress.ip_network(network_key, strict=False)
                    if ip in network:
                        return network_key
                except ValueError:
                    continue
            
            return None
        except ValueError:
            return None
    
    def get_device_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get device information from cache"""
        try:
            with self.lock:
                network_key = self.get_network_key(ip_address)
                if network_key:
                    networks = self.cache_data.get("networks", {})
                    network_data = networks.get(network_key, {})
                    devices = network_data.get("devices", {})
                    return devices.get(ip_address)
                return None
        except Exception as e:
            self.logger.error(f"Error getting device info for {ip_address}: {e}")
            return None
    
    def get_device_by_mac(self, mac_address: str) -> Optional[Dict[str, Any]]:
        """Get device information by MAC address"""
        try:
            with self.lock:
                mac_address = mac_address.upper()
                
                # Search all networks for the MAC address
                for network_data in self.cache_data.get("networks", {}).values():
                    for ip_address, device_data in network_data.get("devices", {}).items():
                        if device_data.get("mac_address", "").upper() == mac_address:
                            return {
                                "ip_address": ip_address,
                                **device_data
                            }
                return None
        except Exception as e:
            self.logger.error(f"Error getting device by MAC {mac_address}: {e}")
            return None
    
    def update_device_info(self, ip_address: str, device_data: Dict[str, Any]) -> bool:
        """Update device information in cache"""
        try:
            with self.lock:
                network_key = self.get_network_key(ip_address)
                
                if not network_key:
                    # Create new network if not exists
                    ip = ipaddress.ip_address(ip_address)
                    if ip.version == 4:
                        # Create /24 network for IPv4
                        network_base = str(ip).rsplit('.', 1)[0] + '.0/24'
                        network_key = network_base
                    else:
                        # For IPv6, use /64 network
                        network_key = str(ipaddress.ip_network(f"{ip}/64", strict=False))
                    
                    # Initialize network structure
                    if "networks" not in self.cache_data:
                        self.cache_data["networks"] = {}
                    
                    self.cache_data["networks"][network_key] = {
                        "name": f"Network {network_key}",
                        "description": f"Auto-created network for {ip_address}",
                        "devices": {}
                    }
                
                # Update device data
                if "networks" not in self.cache_data:
                    self.cache_data["networks"] = {}
                if network_key not in self.cache_data["networks"]:
                    self.cache_data["networks"][network_key] = {"devices": {}}
                if "devices" not in self.cache_data["networks"][network_key]:
                    self.cache_data["networks"][network_key]["devices"] = {}
                
                # Add timestamp
                device_data["last_seen"] = datetime.now().isoformat()
                
                # Update device
                self.cache_data["networks"][network_key]["devices"][ip_address] = device_data
                
                # Save to file
                return self.save_cache()
                
        except Exception as e:
            self.logger.error(f"Error updating device info for {ip_address}: {e}")
            return False
    
    def update_custom_name(self, ip_address: str, custom_name: str) -> bool:
        """Update custom name for a device"""
        try:
            with self.lock:
                device_info = self.get_device_info(ip_address)
                if device_info:
                    device_info["custom_name"] = custom_name
                    return self.update_device_info(ip_address, device_info)
                else:
                    # Create new device entry with just custom name
                    device_data = {
                        "custom_name": custom_name,
                        "hostname": custom_name,
                        "mac_address": "",
                        "manufacturer": "Unknown",
                        "device_type": "unknown",
                        "services": [],
                        "description": "User-named device",
                        "is_cached": False
                    }
                    return self.update_device_info(ip_address, device_data)
        except Exception as e:
            self.logger.error(f"Error updating custom name for {ip_address}: {e}")
            return False
    
    def update_custom_name_by_mac(self, mac_address: str, custom_name: str) -> bool:
        """Update custom name for a device by MAC address"""
        try:
            with self.lock:
                device_info = self.get_device_by_mac(mac_address)
                if device_info:
                    ip_address = device_info["ip_address"]
                    return self.update_custom_name(ip_address, custom_name)
                else:
                    self.logger.warning(f"Device with MAC {mac_address} not found in cache")
                    return False
        except Exception as e:
            self.logger.error(f"Error updating custom name by MAC {mac_address}: {e}")
            return False
    
    def get_network_devices(self, network_key: str) -> Dict[str, Any]:
        """Get all devices in a network"""
        try:
            with self.lock:
                networks = self.cache_data.get("networks", {})
                network_data = networks.get(network_key, {})
                return network_data.get("devices", {})
        except Exception as e:
            self.logger.error(f"Error getting network devices for {network_key}: {e}")
            return {}
    
    def get_devices_in_range(self, start_ip: str, end_ip: str) -> Dict[str, Any]:
        """Get devices in IP range"""
        try:
            with self.lock:
                devices = {}
                
                start = ipaddress.ip_address(start_ip)
                end = ipaddress.ip_address(end_ip)
                
                # Check all networks
                for network_key, network_data in self.cache_data.get("networks", {}).items():
                    for ip_str, device_data in network_data.get("devices", {}).items():
                        try:
                            ip = ipaddress.ip_address(ip_str)
                            if start <= ip <= end:
                                devices[ip_str] = device_data
                        except ValueError:
                            continue
                
                return devices
        except Exception as e:
            self.logger.error(f"Error getting devices in range {start_ip}-{end_ip}: {e}")
            return {}
    
    def is_stoyanov_network(self, start_ip: str, end_ip: str) -> bool:
        """Check if the range matches Stoyanov network"""
        try:
            start = ipaddress.ip_address(start_ip)
            end = ipaddress.ip_address(end_ip)
            
            # Check if range includes Stoyanov network
            stoyanov_network = ipaddress.ip_network("155.235.81.0/24")
            
            return (start in stoyanov_network and end in stoyanov_network) or \
                   (start <= stoyanov_network.network_address and end >= stoyanov_network.broadcast_address)
        except ValueError:
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self.lock:
                stats = {
                    "total_networks": len(self.cache_data.get("networks", {})),
                    "total_devices": 0,
                    "networks": {}
                }
                
                for network_key, network_data in self.cache_data.get("networks", {}).items():
                    device_count = len(network_data.get("devices", {}))
                    stats["total_devices"] += device_count
                    stats["networks"][network_key] = {
                        "name": network_data.get("name", network_key),
                        "device_count": device_count
                    }
                
                return stats
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def get_all_devices(self) -> Dict[str, Any]:
        """Retrieve all devices from all networks"""
        try:
            with self.lock:
                all_devices = {}
                for network_data in self.cache_data.get("networks", {}).values():
                    all_devices.update(network_data.get("devices", {}))
                return all_devices
        except Exception as e:
            self.logger.error(f"Error retrieving all devices: {e}")
            return {}
    
    def update_device_ip_by_mac(self, mac_address: str, new_ip: str) -> bool:
        """Update device IP address for a device identified by MAC address"""
        try:
            with self.lock:
                mac_address = mac_address.upper()
                self.logger.info(f"Attempting to update IP address for MAC {mac_address} to {new_ip}")
                
                # Find the device by MAC address across all networks
                old_ip = None
                old_device_data = None
                old_network_key = None
                
                for network_key, network_data in self.cache_data.get("networks", {}).items():
                    for ip_str, device_data in network_data.get("devices", {}).items():
                        if device_data.get("mac_address", "").upper() == mac_address:
                            old_ip = ip_str
                            old_device_data = device_data.copy()
                            old_network_key = network_key
                            break
                    if old_ip:
                        break
                
                if not old_ip or not old_device_data:
                    self.logger.warning(f"Device with MAC {mac_address} not found in cache for IP update")
                    return False
                
                if old_ip == new_ip:
                    self.logger.info(f"Device MAC {mac_address} already has IP {new_ip}, no update needed")
                    return True
                
                self.logger.info(f"Found device with MAC {mac_address} at old IP {old_ip}, updating to {new_ip}")
                
                # Update the device data with new IP
                old_device_data["ip_address"] = new_ip
                old_device_data["last_seen"] = datetime.now().isoformat()
                
                # Determine which network the new IP belongs to
                new_network_key = self.get_network_key_for_ip(new_ip)
                if not new_network_key:
                    self.logger.warning(f"Could not determine network for new IP {new_ip}")
                    new_network_key = old_network_key  # Keep in same network
                
                # Remove from old location
                if old_network_key in self.cache_data.get("networks", {}):
                    if old_ip in self.cache_data["networks"][old_network_key].get("devices", {}):
                        del self.cache_data["networks"][old_network_key]["devices"][old_ip]
                        self.logger.info(f"Removed old entry for {old_ip} from network {old_network_key}")
                
                # Add to new location
                if new_network_key not in self.cache_data.get("networks", {}):
                    self.cache_data.setdefault("networks", {})[new_network_key] = {
                        "name": new_network_key,
                        "devices": {}
                    }
                
                self.cache_data["networks"][new_network_key]["devices"][new_ip] = old_device_data
                self.logger.info(f"Added updated entry for {new_ip} to network {new_network_key}")
                
                # Save cache
                self.save_cache()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating device IP by MAC {mac_address} to {new_ip}: {e}")
            return False
    
    def get_network_key_for_ip(self, ip_address: str) -> Optional[str]:
        """Determine which network key an IP address belongs to"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check common network patterns
            if str(ip).startswith("10.0.0."):
                return "10.0.0.0/24"
            elif str(ip).startswith("192.168."):
                octets = str(ip).split('.')
                return f"192.168.{octets[2]}.0/24"
            elif str(ip).startswith("155.235.81."):
                return "stoyanov-network"
            else:
                # Default network key based on first 3 octets
                octets = str(ip).split('.')
                return f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
                
        except ValueError:
            return None
    
    def cleanup_invalid_devices(self) -> int:
        """Remove multicast/broadcast addresses and invalid devices from cache"""
        removed_count = 0
        try:
            with self.lock:
                networks_to_remove = []
                for network_key, network_data in self.cache_data.get("networks", {}).items():
                    devices_to_remove = []
                    
                    for ip_str, device_data in network_data.get("devices", {}).items():
                        should_remove = False
                        
                        try:
                            # Check IP address validity
                            ip_obj = ipaddress.ip_address(ip_str)
                            if (ip_obj.is_multicast or 
                                ip_str.endswith('.255') or 
                                ip_str == '255.255.255.255' or
                                ip_str.startswith('224.') or
                                ip_str.startswith('239.')):
                                should_remove = True
                                self.logger.info(f"Removing multicast/broadcast IP: {ip_str}")
                        except ValueError:
                            should_remove = True
                            self.logger.info(f"Removing invalid IP: {ip_str}")
                        
                        # Check MAC address validity
                        mac_address = device_data.get('mac_address', '')
                        if (not mac_address or 
                            mac_address.upper() in ['FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00', 'UNKNOWN', 'N/A'] or
                            mac_address.upper().startswith('01:00:5E') or
                            mac_address.upper().startswith('01-00-5E')):
                            should_remove = True
                            self.logger.info(f"Removing device with invalid/multicast MAC: {ip_str} - {mac_address}")
                        
                        if should_remove:
                            devices_to_remove.append(ip_str)
                            removed_count += 1
                    
                    # Remove invalid devices
                    for ip_str in devices_to_remove:
                        del network_data["devices"][ip_str]
                    
                    # Remove empty networks
                    if not network_data.get("devices"):
                        networks_to_remove.append(network_key)
                
                # Remove empty networks
                for network_key in networks_to_remove:
                    del self.cache_data["networks"][network_key]
                    self.logger.info(f"Removed empty network: {network_key}")
                
                if removed_count > 0:
                    self.save_cache()
                    self.logger.info(f"Cache cleanup completed: removed {removed_count} invalid devices")
                
                return removed_count
                
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
            return 0
