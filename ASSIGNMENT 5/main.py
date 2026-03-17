from fastapi import FastAPI, Query
from pydantic import BaseModel
# Create FastAPI app instance
app = FastAPI()

# Sample product data (acts like a database)
products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook',       'price':  99, 'category': 'Stationery',  'in_stock': True},
    {'id': 3, 'name': 'USB Hub',        'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',        'price':  49, 'category': 'Stationery',  'in_stock': True},
]

# ---------- Orders Storage ----------
orders = []
order_counter = 1

# ---------- Request Model ----------
class OrderRequest(BaseModel):
    customer_name: str
    product_id: int
    quantity: int
    delivery_address: str

# ---------- Helper Function ----------
def find_product(product_id: int):
    for p in products:
        if p['id'] == product_id:
            return p
    return None


# Search endpoint
@app.get('/products/search')
def search_products(keyword: str = Query(...)):
    # Loop through products and check if keyword is present in product name
    # .lower() is used to make search case-insensitive
    results = [
        p for p in products
        if keyword.lower() in p['name'].lower()
    ]

    # If no matching products found
    if not results:
        return {
            "message": f"No products found for: {keyword}",  # Show message
            "results": []  # Return empty list
        }

    # If products found, return details
    return {
        "keyword": keyword,                # What user searched
        "total_found": len(results),       # Number of matching products
        "results": results                # List of matching products
    }
    
@app.get('/products/sort')
def sort_products(
    sort_by: str = Query('price', description='price or name'),  # Default sort field = price
    order:   str = Query('asc',   description='asc or desc'),    # Default order = ascending
):
    # Validate sort_by parameter (only allow 'price' or 'name')
    if sort_by not in ['price', 'name']:
        return {'error': "sort_by must be 'price' or 'name'"}

    # Validate order parameter (only allow 'asc' or 'desc')
    if order not in ['asc', 'desc']:
        return {'error': "order must be 'asc' or 'desc'"}

    # Determine sorting direction
    # If order is 'desc', reverse=True (high → low)
    # If order is 'asc', reverse=False (low → high)
    reverse = (order == 'desc')

    # Sort the products list based on selected field (price or name)
    # key=lambda p: p[sort_by] → tells Python which field to compare
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)

    # Return sorted result with metadata
    return {
        'sort_by': sort_by,         # Field used for sorting
        'order': order,             # Sorting order
        'products': sorted_products # Sorted product list
    }
    
    
@app.get('/products/page')
def get_products_paged(
    page:  int = Query(1, ge=1,  description='Page number'),        # Default page = 1
    limit: int = Query(2, ge=1, le=20, description='Items per page') # Default limit = 2
):
    # Calculate starting index
    # Example: page=2, limit=2 → start = (2-1)*2 = 2
    start = (page - 1) * limit

    # Calculate ending index
    end = start + limit

    # Slice the products list to get only required items
    paged = products[start:end]

    # Return paginated response
    return {
        'page': page,                        # Current page number
        'limit': limit,                      # Items per page
        'total': len(products),              # Total number of products
        'total_pages': -(-len(products) // limit),  # Ceiling division
        'products': paged,                   # Products for this page
    }
    
    
# ---------- Create Order ----------
@app.post('/orders')
def place_order(order_data: OrderRequest):
    global order_counter

    product = find_product(order_data.product_id)

    if not product:
        return {"error": "Product not found"}

    if not product['in_stock']:
        return {"error": f"{product['name']} is out of stock"}

    total_price = product['price'] * order_data.quantity

    order = {
        "order_id": order_counter,
        "customer_name": order_data.customer_name,
        "product": product['name'],
        "quantity": order_data.quantity,
        "delivery_address": order_data.delivery_address,
        "total_price": total_price
    }

    orders.append(order)
    order_counter += 1

    return {"message": "Order placed successfully", "order": order}

# ---------- Search Orders ----------
@app.get('/orders/search')
def search_orders(customer_name: str = Query(...)):
    # Case-insensitive search
    results = [
        o for o in orders
        if customer_name.lower() in o['customer_name'].lower()
    ]

    # No results case
    if not results:
        return {
            "message": f"No orders found for: {customer_name}",
            "orders": []
        }

    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results
    }
    
@app.get('/products/sort-by-category')
def sort_by_category():
    # Sort products by category (A→Z) and then by price (low → high)
    # key returns a tuple → (category, price)
    # Python sorts first by category, then by price within same category
    sorted_products = sorted(products, key=lambda p: (p['category'], p['price']))

    return {
        "total": len(sorted_products),
        "products": sorted_products
    }
    
@app.get('/products/browse')
def browse_products(
    keyword: str = Query(None),                         # Optional search keyword
    sort_by: str = Query('price'),                      # Default sort by price
    order: str = Query('asc'),                          # Default ascending
    page: int = Query(1, ge=1),                         # Default page 1
    limit: int = Query(4, ge=1, le=20),                 # Default 4 items per page
):
    # -------------------------------
    # Step 1: Filter (Search)
    # -------------------------------
    result = products

    if keyword:
        # Case-insensitive search
        result = [
            p for p in result
            if keyword.lower() in p['name'].lower()
        ]

    # -------------------------------
    # Step 2: Sort
    # -------------------------------
    if sort_by not in ['price', 'name']:
        return {"error": "sort_by must be 'price' or 'name'"}

    if order not in ['asc', 'desc']:
        return {"error": "order must be 'asc' or 'desc'"}

    result = sorted(
        result,
        key=lambda p: p[sort_by],
        reverse=(order == 'desc')   # True → desc, False → asc
    )

    # -------------------------------
    # Step 3: Pagination
    # -------------------------------
    total = len(result)

    start = (page - 1) * limit
    end = start + limit

    paged = result[start:end]

    # -------------------------------
    # Final Response
    # -------------------------------
    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": -(-total // limit),   # Ceiling division
        "products": paged
    }
    
    
@app.get('/orders/page')
def get_orders_paged(
    page: int = Query(1, ge=1),          # Default page = 1
    limit: int = Query(3, ge=1, le=20),  # Default limit = 3
):
    # Calculate starting index
    start = (page - 1) * limit

    # Calculate ending index
    end = start + limit

    # Slice orders list for pagination
    paged_orders = orders[start:end]

    # Return paginated orders
    return {
        "page": page,                           # Current page
        "limit": limit,                         # Orders per page
        "total": len(orders),                   # Total orders
        "total_pages": -(-len(orders) // limit),# Ceiling division
        "orders": paged_orders                  # Orders for this page
    }