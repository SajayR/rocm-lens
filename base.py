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

def get_gpu_info(gpu_handle):
    info = {}
    try:
        asic_info = amdsmi_get_gpu_asic_info(gpu_handle)
        info["product_name"] = asic_info.get('market_name', 'N/A')
        if info["product_name"] == "N/A":
            board_info = amdsmi_get_gpu_board_info(gpu_handle)
            info["product_name"] = board_info.get('product_name', 'Unknown GPU')
    except Exception:
        info["product_name"] = "Unknown GPU"
    
    # GPU ID and BDF
    info["bdf"] = "N/A"
    try:
        info["bdf"] = amdsmi_get_gpu_device_bdf(gpu_handle)
    except Exception:
        pass
    
    # Temperature
    info["gpu_temp"] = "N/A"
    info["mem_temp"] = "N/A"
    try:
        info["gpu_temp"] = amdsmi_get_temp_metric(gpu_handle, AmdSmiTemperatureType.EDGE, AmdSmiTemperatureMetric.CURRENT)
    except Exception:
        pass
    try:
        info["mem_temp"] = amdsmi_get_temp_metric(gpu_handle, AmdSmiTemperatureType.VRAM, AmdSmiTemperatureMetric.CURRENT)
    except Exception:
        pass
    
    # Activity/Utilization
    info["gpu_util"] = "N/A"
    info["mem_util"] = "N/A"
    try:
        util_data = amdsmi_get_gpu_activity(gpu_handle)
        info["gpu_util"] = util_data.get('gfx_activity', "N/A")
        info["mem_util"] = util_data.get('umc_activity', "N/A")
    except Exception:
        pass
    
    # Clock speeds
    info["gpu_clock"] = "N/A"
    info["mem_clock"] = "N/A"
    try:
        gpu_clock_info = amdsmi_get_clock_info(gpu_handle, AmdSmiClkType.GFX)
        info["gpu_clock"] = gpu_clock_info.get('clk', "N/A")
    except Exception:
        pass
    try:
        mem_clock_info = amdsmi_get_clock_info(gpu_handle, AmdSmiClkType.MEM)
        info["mem_clock"] = mem_clock_info.get('clk', "N/A")
    except Exception:
        pass
    
    # Power
    info["power"] = "N/A"
    try:
        power_info = amdsmi_get_power_info(gpu_handle)
        info["power"] = power_info.get('current_socket_power', "N/A")
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
    
    # Fan speed
    info["fan_speed"] = "N/A"
    try:
        info["fan_speed"] = amdsmi_get_gpu_fan_speed(gpu_handle, 0)
    except Exception:
        pass
    
    # ECC errors
    info["single_ecc"] = "N/A"
    info["double_ecc"] = "N/A"
    try:
        ecc_info = amdsmi_get_gpu_total_ecc_count(gpu_handle)
        info["single_ecc"] = ecc_info.get('correctable_count', "N/A")
        info["double_ecc"] = ecc_info.get('uncorrectable_count', "N/A")
    except Exception:
        pass
    
    # PCIE info
    info["pcie_width"] = "N/A"
    info["pcie_speed"] = "N/A"
    try:
        pcie_info = amdsmi_get_pcie_info(gpu_handle)
        pcie_metric = pcie_info.get('pcie_metric', {})
        info["pcie_width"] = pcie_metric.get('pcie_width', "N/A")
        info["pcie_speed"] = pcie_metric.get('pcie_speed', "N/A")
    except Exception:
        pass
    
    return info

def print_gpu_info(gpu_index, info):
    print(f"\n{'='*50}")
    print(f"GPU {gpu_index}: {info['product_name']} ({info['bdf']})")
    print(f"{'='*50}")
    sections = {
        "Utilization": [
            ("GPU Utilization", info["gpu_util"], "%"),
            ("Memory Utilization", info["mem_util"], "%"),
        ],
        "Temperature": [
            ("GPU Temperature", info["gpu_temp"], "°C"),
            ("Memory Temperature", info["mem_temp"], "°C"),
        ],
        "Clocks": [
            ("GPU Clock", info["gpu_clock"], "MHz"),
            ("Memory Clock", info["mem_clock"], "MHz"),
        ],
        "Memory": [
            ("VRAM Used", info["vram_used"], "MB"),
            ("VRAM Total", info["vram_total"], "MB"),
            ("Usage", 
             "N/A" if info["vram_used"] == "N/A" or info["vram_total"] == "N/A" 
             else f"{(100 * info['vram_used'] / info['vram_total']):.1f}", "%"),
        ],
        "Power & Cooling": [
            ("Power Consumption", info["power"], "W"),
            ("Fan Speed", info["fan_speed"], "%"),
        ],
        "PCIe": [
            ("Width", info["pcie_width"], "lanes"),
            ("Speed", info["pcie_speed"], "GT/s"),
        ],
        "Errors": [
            ("Single Bit ECC Errors", info["single_ecc"], ""),
            ("Double Bit ECC Errors", info["double_ecc"], ""),
        ]
    }
    
    all_metrics = [metric for section_metrics in sections.values() for metric in section_metrics]
    max_label_length = max(len(label) for label, _, _ in all_metrics)
    for section_name, metrics in sections.items():
        print(f"\n{section_name}:")
        for label, value, unit in metrics:
            formatted_value = format_value(value, unit)
            print(f"  {label.ljust(max_label_length)} : {formatted_value}")

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