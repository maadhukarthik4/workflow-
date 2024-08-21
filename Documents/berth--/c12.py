import requests

def fetch_json(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def fetch_resource_id(api_url, bearer_token):
    url = f"{api_url}/wms-server/api/v1/advancedShippingNoticeLines"
    headers = {'Authorization': f'Bearer {bearer_token}'}
    return fetch_json(url, headers)

def fetch_container_descriptors(api_url, bearer_token):
    url = f"{api_url}/wms-server/api/v1/containers"
    headers = {'Authorization': f'Bearer {bearer_token}'}
    return fetch_json(url, headers)

def fetch_inventory_transactions(api_url, bearer_token):
    url = f"{api_url}/wms-server/api/v1/inventoryTransactions?page=1&size=50"
    headers = {'Authorization': f'Bearer {bearer_token}'}
    return fetch_json(url, headers)

def create_payload(resource_id, container_id, container_name, quantity, type, container_partition_index):
    payload = {
        "user": "string",  # Replace "string" with the actual user value if needed
        "quantity": quantity,
        "itemExpirationDate": "2024-08-20",  # Replace with the actual expiration date
        "resourceId": resource_id,
        "type": type,
        "container": {
            "id": container_id,
            "name": container_name  # Include container name
        },
        "containerPartitionIndex": container_partition_index
    }
    return payload

def send_to_api(url, payload, headers):
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def print_filtered_inventory_transactions(api_url, bearer_token):
    inventory_data = fetch_inventory_transactions(api_url, bearer_token)
    if inventory_data is None:
        print("Failed to fetch inventory transactions.")
        return

    # Print filtered items in vertical format
    for item in inventory_data.get('items', []):
        print("ID:", item.get('id', 'N/A'))
        print("Item Code:", item.get('itemCode', 'N/A'))
        print("Owner Code:", item.get('ownerCode', 'N/A'))
        print("Item Lot Number:", item.get('itemLotNumber', 'N/A'))
        print("Container Name:", item.get('destinationContainerName', 'N/A'))
        print("Quantity:", item.get('quantity', 'N/A'))
        print("User:", item.get('user', 'N/A'))
        print("-" * 30)  # Separator between items

def main():
    api_url = "http://localhost"
    bearer_token = "autobootstrap"

    # Fetch container descriptors
    container_data = fetch_container_descriptors(api_url, bearer_token)
    if container_data is None:
        return

    container_ids = []
    bin_limits = {}
    container_names = {}
    partition_indices = {}

    for item in container_data.get('items', []):
        container_id = item.get('id')
        descriptor_name = item.get('descriptor', {}).get('name', 'Unknown')
        container_name = item.get('name', 'Unknown')
        container_ids.append(container_id)
        container_names[container_id] = container_name

        if descriptor_name == 'Bin 1x1':
            bin_limits[container_id] = 1  # Limit for Bin 1x1
            partition_indices[container_id] = 1  # Assign partition index for Bin 1x1
        elif descriptor_name == 'Bin 2x1':
            bin_limits[container_id] = 4  # Limit for Bin 2x1
            partition_indices[container_id] = 2  # Assign partition index for Bin 2x1
        elif descriptor_name == 'Bin 2x2':
            bin_limits[container_id] = 9  # Limit for Bin 2x2
            partition_indices[container_id] = 3  # Assign partition index for Bin 2x2

    # Fetch resource IDs
    resource_data = fetch_resource_id(api_url, bearer_token)
    if resource_data is None:
        return

    resource_ids = [item['id'] for item in resource_data.get('items', [])]

    if not resource_ids or not container_ids:
        return

    headers = {'Authorization': f'Bearer {bearer_token}'}
    
    for container_id in container_ids:
        container_name = container_names.get(container_id, 'Unknown')
        quantity = bin_limits.get(container_id, 9)  # Default to 9 if not found
        container_partition_index = partition_indices.get(container_id, 1)  # Default to 1 if not found

        for resource_id in resource_ids:
            # Create and send payload for RECEIVE_USABLE
            payload = create_payload(resource_id, container_id, container_name, quantity, "RECEIVE_USABLE", container_partition_index)
            response = send_to_api(f"{api_url}/wms-server/api/v1/advancedShippingNoticeInventoryTransactions", payload, headers)
            
            if response:
                # If the quantity matches, create and send ACCEPT_USABLE payload
                if response.get('quantity') == quantity:
                    payload_accept = create_payload(resource_id, container_id, container_name, quantity, "ACCEPT_USABLE", container_partition_index)
                    send_to_api(f"{api_url}/wms-server/api/v1/advancedShippingNoticeInventoryTransactions", payload_accept, headers)

    # Fetch and print filtered items from inventory transactions
    print_filtered_inventory_transactions(api_url, bearer_token)

if __name__ == "__main__":
    main()
