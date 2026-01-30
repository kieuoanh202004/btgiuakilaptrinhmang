from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import models, schemas, databaseaa
from app.database import engine, SessionLocal

# --- KHỞI TẠO DATABASE ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Elearning 4",
    description="Hệ thống quản lý hàng hóa nhập xuất kho chuyên nghiệp",
    version="2.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- GIAO DIỆN NGƯỜI DÙNG (Dễ sử dụng) ---
@app.get("/interface", response_class=HTMLResponse, tags=["Giao diện"])
def get_interface():
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <title>Kho Hàng E4 - Tiếng Việt</title>
        <style>
            body { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
            .navbar { background: #2c3e50; color: white; padding: 15px; }
            .card { border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 10px; }
            .btn-primary { background: #1abc9c; border: none; }
            .btn-primary:hover { background: #16a085; }
            th { background-color: #34495e; color: white; }
        </style>
    </head>
    <body>
        <div class="navbar"><h3>📦 QUẢN LÝ KHO E4 - PHIÊN BẢN TIẾNG VIỆT</h3></div>
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-4">
                    <div class="card p-4">
                        <h4 class="text-center">Nhập Hàng</h4>
                        <input type="text" id="name" class="form-control mb-2" placeholder="Tên sản phẩm">
                        <input type="text" id="sku" class="form-control mb-2" placeholder="Mã SKU (Mã vạch)">
                        <input type="number" id="qty" class="form-control mb-2" placeholder="Số lượng nhập">
                        <input type="number" id="price" class="form-control mb-3" placeholder="Giá bán (VNĐ)">
                        <button class="btn btn-primary w-100" onclick="addProduct()">XÁC NHẬN NHẬP KHO</button>
                    </div>
                </div>
                <div class="col-md-8">
                    <div class="card p-4">
                        <h4 class="text-center">Danh Sách Hàng Tồn</h4>
                        <table class="table table-hover mt-3">
                            <thead>
                                <tr>
                                    <th>Mã SKU</th>
                                    <th>Tên Hàng</th>
                                    <th>Số Lượng</th>
                                    <th>Đơn Giá</th>
                                    <th>Hành Động</th>
                                </tr>
                            </thead>
                            <tbody id="inventoryBody"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <script>
            async function loadData() {
                const res = await fetch('/products');
                const result = await res.json();
                const tbody = document.getElementById('inventoryBody');
                tbody.innerHTML = result.data.map(p => `
                    <tr>
                        <td><b>${p.sku}</b></td>
                        <td>${p.name}</td>
                        <td><span class="badge bg-warning text-dark">${p.quantity}</span></td>
                        <td>${p.price.toLocaleString()} đ</td>
                        <td><button class="btn btn-danger btn-sm" onclick="deleteItem(${p.id})">Xóa</button></td>
                    </tr>`).join('');
            }
            async function addProduct() {
                const data = {
                    name: document.getElementById('name').value,
                    sku: document.getElementById('sku').value,
                    quantity: parseInt(document.getElementById('qty').value),
                    price: parseFloat(document.getElementById('price').value)
                };
                await fetch('/products', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                alert("Đã thêm hàng vào kho!");
                loadData();
            }
            async function deleteItem(id) {
                if(confirm("Bạn có chắc chắn muốn xóa mặt hàng này?")) {
                    await fetch(`/products/${id}`, { method: 'DELETE' });
                    loadData();
                }
            }
            loadData();
        </script>
    </body>
    </html>
    """

# --- CÁC API TIẾNG VIỆT ---

@app.get("/", tags=["Hệ thống"], summary="Kiểm tra kết nối")
def root():
    return {"thong_bao": "Hệ thống đang hoạt động!"}

@app.get("/products", tags=["Kho hàng"], summary="Lấy danh sách sản phẩm")
def get_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return {"success": True, "data": products}

@app.post("/products", tags=["Kho hàng"], summary="Thêm sản phẩm mới")
def create_product(item: schemas.ProductCreate, db: Session = Depends(get_db)):
    new_item = models.Product(name=item.name, sku=item.sku, quantity=item.quantity, price=item.price)
    db.add(new_item)
    db.commit()
    return {"success": True, "message": "Đã thêm hàng thành công"}

@app.delete("/products/{id}", tags=["Kho hàng"], summary="Xóa sản phẩm")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Product).filter(models.Product.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Không tìm thấy mặt hàng này")
    db.delete(db_item)
    db.commit()
    return {"success": True, "message": "Đã xóa thành công"}