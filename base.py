#!/usr/bin/env python3
import os
import sys
import amdsmi
from amdsmi import *

def format_value(value, unit="", divisor=1):
    if value == "N/A" or value is None:
        return "N/A"
    try:
        # Format numeric values with proper divisor
        numeric_value = float(value) / divisor
        if numeric_value.is_integer():
            numeric_value = int(numeric_value)
        return f"{numeric_value} {unit}".strip()
    except (ValueError, TypeError):
        return f"{value} {unit}".strip()

def format_bytes(bytes_value, use_binary=True):
    if bytes_value == "N/A" or bytes_value is None:
        return "N/A"
    
    try:
        bytes_value = float(bytes_value)
        if use_binary:
            # Binary (1024-based)
            units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
            divisor = 1024
        else:
            # Decimal (1000-based)
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            divisor = 1000
            
        unit_index = 0
        while bytes_value >= divisor and unit_index < len(units) - 1:
            bytes_value /= divisor
            unit_index += 1
            
        return f"{bytes_value:.2f} {units[unit_index]}"
    except (ValueError, TypeError):
        return f"{bytes_value} B"

def get_gpu_info(gpu_handle):
    info = {}
    try:
        asic_info = amdsmi_get_gpu_asic_info(gpu_handle)
        info["product_name"] = asic_info.get('market_name', 'N/A')
        info["vendor_name"] = asic_info.get('vendor_name', 'N/A')
        info["device_id"] = asic_info.get('device_id', 'N/A')
        info["compute_units"] = asic_info.get('num_of_compute_units', 'N/A')
        info["gfx_version"] = asic_info.get('target_graphics_version', 'N/A')
        
        if info["product_name"] == "N/A":
            board_info = amdsmi_get_gpu_board_info(gpu_handle)
            info["product_name"] = board_info.get('product_name', 'Unknown GPU')
            info["manufacturer"] = board_info.get('manufacturer_name', 'N/A')
            info["serial"] = board_info.get('product_serial', 'N/A')
    except Exception:
        info["product_name"] = "Unknown GPU"
    
    # Device UUID
    info["uuid"] = "N/A"
    try:
        info["uuid"] = amdsmi_get_gpu_device_uuid(gpu_handle)
    except Exception:
        pass
    # GPU ID and BDF
    info["bdf"] = "N/A"
    try:
        info["bdf"] = amdsmi_get_gpu_device_bdf(gpu_handle)
    except Exception:
        pass
    # Driver info
    info["driver_version"] = "N/A"
    info["driver_date"] = "N/A"
    try:
        driver_info = amdsmi_get_gpu_driver_info(gpu_handle)
        info["driver_version"] = driver_info.get('driver_version', 'N/A')
        info["driver_date"] = driver_info.get('driver_date', 'N/A')
    except Exception:
        pass
    # VBIOS info
    info["vbios_version"] = "N/A"
    info["vbios_date"] = "N/A"
    try:
        vbios_info = amdsmi_get_gpu_vbios_info(gpu_handle)
        info["vbios_version"] = vbios_info.get('version', 'N/A')
        info["vbios_date"] = vbios_info.get('build_date', 'N/A')
    except Exception:
        pass
    # Firmware versions
    info["firmware_info"] = "N/A"
    try:
        fw_info = amdsmi_get_fw_info(gpu_handle)
        if 'fw_list' in fw_info and fw_info['fw_list']:
            info["firmware_info"] = fw_info
    except Exception:
        pass
    # Temperature (multiple sensors)
    info["edge_temp"] = "N/A"
    info["junction_temp"] = "N/A"
    info["mem_temp"] = "N/A"
    try:
        info["edge_temp"] = amdsmi_get_temp_metric(gpu_handle, AmdSmiTemperatureType.EDGE, AmdSmiTemperatureMetric.CURRENT)
        info["junction_temp"] = amdsmi_get_temp_metric(gpu_handle, AmdSmiTemperatureType.JUNCTION, AmdSmiTemperatureMetric.CURRENT)
        info["mem_temp"] = amdsmi_get_temp_metric(gpu_handle, AmdSmiTemperatureType.VRAM, AmdSmiTemperatureMetric.CURRENT)
    except Exception:
        pass
    # Thermal limits
    info["critical_temp"] = "N/A"
    try:
        info["critical_temp"] = amdsmi_get_temp_metric(gpu_handle, AmdSmiTemperatureType.EDGE, AmdSmiTemperatureMetric.CRITICAL)
    except Exception:
        pass
    # Activity/Utilization
    info["gpu_util"] = "N/A"
    info["mem_util"] = "N/A"
    info["mm_util"] = "N/A"
    try:
        util_data = amdsmi_get_gpu_activity(gpu_handle)
        info["gpu_util"] = util_data.get('gfx_activity', "N/A")
        info["mem_util"] = util_data.get('umc_activity', "N/A")
        info["mm_util"] = util_data.get('mm_activity', "N/A")
    except Exception:
        pass

    info["encoder_util"] = "N/A"
    info["decoder_util"] = "N/A"
    try:
        metrics = amdsmi_get_gpu_metrics_info(gpu_handle)
       
        if metrics:
            if 'vcn_activity' in metrics and isinstance(metrics['vcn_activity'], list) and metrics['vcn_activity']:
                # Average all VCN activity values that aren't N/A
                valid_values = [v for v in metrics['vcn_activity'] if v != "N/A"]
                if valid_values:
                    info["encoder_util"] = sum(valid_values) / len(valid_values)
    except Exception:
        pass
    info["gpu_clock"] = "N/A"
    info["gpu_clock_min"] = "N/A"
    info["gpu_clock_max"] = "N/A"
    info["mem_clock"] = "N/A"
    info["mem_clock_min"] = "N/A"
    info["mem_clock_max"] = "N/A"
    
    try:
        gpu_clock_info = amdsmi_get_clock_info(gpu_handle, AmdSmiClkType.GFX)
        info["gpu_clock"] = gpu_clock_info.get('clk', "N/A")
        info["gpu_clock_min"] = gpu_clock_info.get('min_clk', "N/A")
        info["gpu_clock_max"] = gpu_clock_info.get('max_clk', "N/A")
    except Exception:
        pass
    
    try:
        mem_clock_info = amdsmi_get_clock_info(gpu_handle, AmdSmiClkType.MEM)
        info["mem_clock"] = mem_clock_info.get('clk', "N/A")
        info["mem_clock_min"] = mem_clock_info.get('min_clk', "N/A")
        info["mem_clock_max"] = mem_clock_info.get('max_clk', "N/A")
    except Exception:
        pass

    try:
        gpu_freqs = amdsmi_get_clk_freq(gpu_handle, AmdSmiClkType.GFX)
        if 'frequency' in gpu_freqs:
            info["gpu_available_freqs"] = gpu_freqs.get('frequency', [])
    except Exception:
        info["gpu_available_freqs"] = []

    info["perf_level"] = "N/A"
    try:
        info["perf_level"] = amdsmi_get_gpu_perf_level(gpu_handle)
    except Exception:
        pass
    
    # Power
    info["power"] = "N/A"
    info["power_avg"] = "N/A"
    info["power_cap"] = "N/A"
    info["power_cap_default"] = "N/A"
    info["power_cap_min"] = "N/A" 
    info["power_cap_max"] = "N/A"
    
    try:
        power_info = amdsmi_get_power_info(gpu_handle)
        info["power"] = power_info.get('current_socket_power', "N/A")
        info["power_avg"] = power_info.get('average_socket_power', "N/A")
        info["power_cap"] = power_info.get('power_limit', "N/A")
    except Exception:
        pass
    
    try:
        # Additional power cap information
        power_cap_info = amdsmi_get_power_cap_info(gpu_handle, 0)
        info["power_cap"] = power_cap_info.get('power_cap', info["power_cap"])
        info["power_cap_default"] = power_cap_info.get('default_power_cap', "N/A")
        info["power_cap_min"] = power_cap_info.get('min_power_cap', "N/A")
        info["power_cap_max"] = power_cap_info.get('max_power_cap', "N/A")
    except Exception:
        pass
    
    # Energy counter (power consumption over time)
    info["energy_counter"] = "N/A"
    try:
        energy_info = amdsmi_get_energy_count(gpu_handle)
        info["energy_counter"] = energy_info.get('energy_accumulator', "N/A")
    except Exception:
        pass
    
    # Voltage
    info["voltage_gfx"] = "N/A"
    info["voltage_soc"] = "N/A"
    info["voltage_mem"] = "N/A"
    try:
        power_info = amdsmi_get_power_info(gpu_handle)
        info["voltage_gfx"] = power_info.get('gfx_voltage', "N/A")
        info["voltage_soc"] = power_info.get('soc_voltage', "N/A")
        info["voltage_mem"] = power_info.get('mem_voltage', "N/A")
    except Exception:
        pass
    
    # VRAM
    info["vram_used"] = "N/A"
    info["vram_total"] = "N/A"
    try:
        vram_info = amdsmi_get_gpu_vram_usage(gpu_handle)
        info["vram_used"] = vram_info.get('vram_used', "N/A")
        info["vram_total"] = vram_info.get('vram_total', "N/A")
    except Exception:
        pass
    
    # VRAM type, vendor, bandwidth
    info["vram_type"] = "N/A"
    info["vram_vendor"] = "N/A"
    info["vram_bit_width"] = "N/A"
    try:
        vram_details = amdsmi_get_gpu_vram_info(gpu_handle)
        if vram_details:
            vram_type_val = vram_details.get('vram_type', "N/A")
            # Convert enum to readable string if possible
            if hasattr(amdsmi, 'amdsmi_wrapper') and hasattr(amdsmi.amdsmi_wrapper, 'amdsmi_vram_type_t__enumvalues'):
                enum_values = amdsmi.amdsmi_wrapper.amdsmi_vram_type_t__enumvalues
                if vram_type_val in enum_values:
                    info["vram_type"] = enum_values[vram_type_val].replace('AMDSMI_VRAM_TYPE_', '')
            else:
                info["vram_type"] = vram_type_val
                
            info["vram_bit_width"] = vram_details.get('vram_bit_width', "N/A")
            try:
                info["vram_vendor"] = amdsmi_get_gpu_vram_vendor(gpu_handle)
            except Exception:
                pass
    except Exception:
        pass
    
    # Fan speed (percentage and RPM)
    info["fan_speed_pct"] = "N/A"
    info["fan_speed_rpm"] = "N/A"
    info["fan_max_rpm"] = "N/A"
    try:
        info["fan_speed_pct"] = amdsmi_get_gpu_fan_speed(gpu_handle, 0)
        info["fan_speed_rpm"] = amdsmi_get_gpu_fan_rpms(gpu_handle, 0)
    except Exception:
        pass
    
    try:
        info["fan_max_rpm"] = amdsmi_get_gpu_fan_speed_max(gpu_handle, 0)
    except Exception:
        pass
    
    # ECC errors
    info["ecc_enabled"] = "N/A"
    info["single_ecc"] = "N/A"
    info["double_ecc"] = "N/A"
    try:
        ecc_enabled = amdsmi_get_gpu_ecc_enabled(gpu_handle)
        info["ecc_enabled"] = bool(ecc_enabled) if ecc_enabled != "N/A" else "N/A"
    except Exception:
        pass
    
    try:
        ecc_info = amdsmi_get_gpu_total_ecc_count(gpu_handle)
        info["single_ecc"] = ecc_info.get('correctable_count', "N/A")
        info["double_ecc"] = ecc_info.get('uncorrectable_count', "N/A")
    except Exception:
        pass
    
    # Memory errors and bad pages
    info["bad_pages"] = "N/A"
    try:
        bad_pages = amdsmi_get_gpu_bad_page_info(gpu_handle)
        info["bad_pages"] = len(bad_pages) if isinstance(bad_pages, list) else "N/A"
    except Exception:
        pass
    
    # PCIE info
    info["pcie_width"] = "N/A"
    info["pcie_speed"] = "N/A"
    info["pcie_max_width"] = "N/A"
    info["pcie_max_speed"] = "N/A"
    info["pcie_replay_count"] = "N/A"
    try:
        pcie_info = amdsmi_get_pcie_info(gpu_handle)
        if 'pcie_metric' in pcie_info:
            metric = pcie_info['pcie_metric']
            info["pcie_width"] = metric.get('pcie_width', "N/A")
            info["pcie_speed"] = metric.get('pcie_speed', "N/A")
            info["pcie_replay_count"] = metric.get('pcie_replay_count', "N/A")
        
        if 'pcie_static' in pcie_info:
            static_info = pcie_info['pcie_static']
            info["pcie_max_width"] = static_info.get('max_pcie_width', "N/A")
            info["pcie_max_speed"] = static_info.get('max_pcie_speed', "N/A")
    except Exception:
        pass
    
    # PCIe bandwidth
    info["pcie_tx"] = "N/A"
    info["pcie_rx"] = "N/A"
    try:
        throughput = amdsmi_get_gpu_pci_throughput(gpu_handle)
        if isinstance(throughput, dict):
            info["pcie_tx"] = throughput.get('sent', "N/A")
            info["pcie_rx"] = throughput.get('received', "N/A")
    except Exception:
        pass
    
    # XGMI info for multi-GPU setups
    info["xgmi_info"] = "N/A"
    try:
        xgmi_info = amdsmi_get_xgmi_info(gpu_handle)
        if xgmi_info:
            info["xgmi_info"] = xgmi_info
    except Exception:
        pass
    
    # NUMA node
    info["numa_node"] = "N/A"
    try:
        info["numa_node"] = amdsmi_topo_get_numa_node_number(gpu_handle)
    except Exception:
        pass
    
    # Throttling or violation status
    info["throttle_status"] = "N/A"
    try:
        violation = amdsmi_get_violation_status(gpu_handle)
        if violation:
            # Check if any active throttling exists
            throttle_types = []
            if violation.get('active_ppt_pwr', False):
                throttle_types.append("Power")
            if violation.get('active_socket_thrm', False):
                throttle_types.append("Thermal")
            if violation.get('active_prochot_thrm', False):
                throttle_types.append("Prochot")
            
            if throttle_types:
                info["throttle_status"] = ", ".join(throttle_types)
            else:
                info["throttle_status"] = "None"
    except Exception:
        pass
    
    info["processes"] = []
    try:
        processes = amdsmi_get_gpu_process_list(gpu_handle)
        if processes:
            info["processes"] = processes
    except Exception:
        pass
    
    return info

def print_gpu_info(gpu_index, info):
    print(f"\n{'='*80}")
    print(f"GPU {gpu_index}: {info['product_name']} ({info['bdf']})")
    print(f"{'='*80}")
    sections = {
        "Identification": [
            ("UUID", info["uuid"], ""),
            ("Device ID", info["device_id"], ""),
            ("Compute Units", info["compute_units"], ""),
            ("Architecture", info["gfx_version"], ""),
            ("Driver Version", info["driver_version"], ""),
            ("VBIOS Version", info["vbios_version"], ""),
        ],
        "Utilization": [
            ("GPU Utilization", info["gpu_util"], "%"),
            ("Memory Utilization", info["mem_util"], "%"),
            ("Multimedia Engine", info["mm_util"], "%"),
            ("Encoder Utilization", info["encoder_util"], "%"),
            ("Decoder Utilization", info["decoder_util"], "%"),
            ("Performance Level", info["perf_level"], ""),
        ],
        "Temperature": [
            ("Edge Temperature", info["edge_temp"], "°C"),
            ("Junction Temperature", info["junction_temp"], "°C"),
            ("Memory Temperature", info["mem_temp"], "°C"),
            ("Critical Limit", info["critical_temp"], "°C"),
            ("Throttling", info["throttle_status"], ""),
        ],
        "Clocks": [
            ("GPU Clock Current", info["gpu_clock"], "MHz"),
            ("GPU Clock Range", f"{info['gpu_clock_min']} - {info['gpu_clock_max']}", "MHz"),
            ("Memory Clock Current", info["mem_clock"], "MHz"),
            ("Memory Clock Range", f"{info['mem_clock_min']} - {info['mem_clock_max']}", "MHz"),
        ],
        "Power": [
            ("Current Consumption", info["power"], "W"),
            ("Average Consumption", info["power_avg"], "W"),
            ("Power Cap", info["power_cap"], "W"),
            ("Power Cap Range", f"{info['power_cap_min']} - {info['power_cap_max']}", "W"),
            ("Default Power Cap", info["power_cap_default"], "W"),
        ],
        "Voltage": [
            ("GPU Voltage", info["voltage_gfx"], "mV"),
            ("SOC Voltage", info["voltage_soc"], "mV"),
            ("Memory Voltage", info["voltage_mem"], "mV"),
        ],
        "Memory": [
            ("Type", info["vram_type"], ""),
            ("Vendor", info["vram_vendor"], ""),
            ("Bus Width", info["vram_bit_width"], "bits"),
            ("VRAM Used", info["vram_used"], "MB"),
            ("VRAM Total", info["vram_total"], "MB"),
            ("Usage Percentage", 
             "N/A" if info["vram_used"] == "N/A" or info["vram_total"] == "N/A" 
             else f"{(100 * float(info['vram_used']) / float(info['vram_total'])):.1f}", "%"),
        ],
        "Cooling": [
            ("Fan Speed", info["fan_speed_pct"], "%"),
            ("Fan RPM", info["fan_speed_rpm"], "RPM"),
            ("Max Fan RPM", info["fan_max_rpm"], "RPM"),
        ],
        "PCIe": [
            ("Current Width", info["pcie_width"], "lanes"),
            ("Current Speed", info["pcie_speed"], "GT/s"),
            ("Maximum Width", info["pcie_max_width"], "lanes"),
            ("Maximum Speed", info["pcie_max_speed"], "GT/s"),
            ("Throughput TX", info["pcie_tx"], "MB/s"),
            ("Throughput RX", info["pcie_rx"], "MB/s"),
            ("Replay Count", info["pcie_replay_count"], ""),
            ("NUMA Node", info["numa_node"], ""),
        ],
        "Reliability": [
            ("ECC Enabled", info["ecc_enabled"], ""),
            ("Single-bit ECC Errors", info["single_ecc"], ""),
            ("Double-bit ECC Errors", info["double_ecc"], ""),
            ("Bad Pages", info["bad_pages"], "pages"),
        ],
    }
    
    all_metrics = [metric for section_metrics in sections.values() for metric in section_metrics]
    max_label_length = max(len(label) for label, _, _ in all_metrics)
    for section_name, metrics in sections.items():
        print(f"\n{section_name}:")
        for label, value, unit in metrics:
            formatted_value = format_value(value, unit)
            print(f"  {label.ljust(max_label_length)} : {formatted_value}")
    if info["processes"] and len(info["processes"]) > 0:
        print("\nProcesses:")
        process_format = "  {pid:>7}  {name:<20}  {vram:>10}  {gpu_usage:>8}  {enc_usage:>8}"
        print(process_format.format(
            pid="PID", 
            name="NAME", 
            vram="VRAM USAGE", 
            gpu_usage="GPU UTIL", 
            enc_usage="ENC UTIL"
        ))
        print("  " + "-" * 60)
        
        for proc in info["processes"]:
            print(process_format.format(
                pid=proc.get('pid', 'N/A'),
                name=proc.get('name', 'N/A')[:20],
                vram=format_bytes(proc.get('memory_usage', {}).get('vram_mem', 'N/A')),
                gpu_usage=f"{proc.get('engine_usage', {}).get('gfx', 'N/A')}%",
                enc_usage=f"{proc.get('engine_usage', {}).get('enc', 'N/A')}%"
            ))

def main():
    try:
        amdsmi_init()
        gpu_handles = amdsmi_get_processor_handles()
        num_gpus = len(gpu_handles)
        
        if num_gpus == 0:
            print("No AMD GPUs detected on this machine")
            return
        
        print(f"Found {num_gpus} AMD GPU(s)")
        for i, gpu_handle in enumerate(gpu_handles):
            try:
                gpu_info = get_gpu_info(gpu_handle)
                print_gpu_info(i, gpu_info)
            except Exception as e:
                print(f"\nError retrieving information for GPU {i}: {str(e)}")
    except Exception as e:
        print(f"Error initializing AMD SMI: {str(e)}")
    finally:
        try:
            amdsmi_shut_down()
        except Exception:
            pass

if __name__ == "__main__":
    main()