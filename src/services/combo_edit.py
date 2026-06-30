from sqlalchemy import select, delete
from datetime import datetime
from src.database.structure import ComboDetail, Combo, Variant, Product, ProductType, ComboVariant

class ComboService:
    def __init__(self, session):
        self.session = session

    def fetch_all_saved_combos(self) -> list:
        """Truy vấn danh sách combo đã lưu từ DB và gom nhóm theo combo_composition_key"""
        stmt = (
            select(
                ComboDetail.combo_variant_key,
                ComboDetail.combo_composition_key,
                Combo.combo_name,
                Variant.variant_name,
                ComboDetail.product_key,
                Product.product_code,
                Product.product_name,
                ComboDetail.product_price,
                ComboDetail.product_quantity,
                ProductType.product_type_name
            )
            .join(ComboVariant, ComboDetail.combo_variant_key == ComboVariant.combo_variant_key)
            .join(Combo, ComboVariant.combo_key == Combo.combo_key)
            .join(Variant, ComboVariant.variant_key == Variant.variant_key)
            .join(Product, ComboDetail.product_key == Product.product_key)
            .join(ProductType, Product.product_type_key == ProductType.product_type_key)
        )
        raw_data = self.session.execute(stmt).all()

        grouped = {}
        for row in raw_data:
            ck = row.combo_composition_key
            if ck not in grouped:
                grouped[ck] = {
                    "combo_variant_key": row.combo_variant_key,
                    "combo_composition_key": ck,
                    "combo_name": row.combo_name,
                    "variant_name": row.variant_name,
                    "products": []
                }
            grouped[ck]["products"].append({
                "product_key": row.product_key,
                "product_code": row.product_code,
                "product_name": row.product_name,
                "product_quantity": int(row.product_quantity),
                "product_price": float(row.product_price),
                "product_type_name": row.product_type_name
            })

        for comp_key, info in grouped.items():
            info["total_combo_value"] = sum(p["product_price"] * p["product_quantity"] for p in info["products"])

        return list(grouped.values())

    def fetch_product_autocomplete_list(self) -> list:
        """Lấy danh sách sản phẩm phục vụ gợi ý tự động trên TableView"""
        return self.session.execute(
            select(Product.product_key, Product.product_code, Product.product_name)
        ).all()

    def update_single_combo(self, variant_key, composition_key, products_list) -> bool:
        """Cập nhật dữ liệu bằng cách Overwrite bản ghi chi tiết cũ của nhóm"""
        current_time = datetime.now()
        try:
            # 1. Xóa các dòng sản phẩm cũ trong DB thuộc nhóm composition_key này
            self.session.execute(
                delete(ComboDetail).where(
                    delete(ComboDetail).where(
                    ComboDetail.combo_variant_key == variant_key,
                    ComboDetail.combo_composition_key == composition_key
                )
                )
            )
            
            # 2. Chèn lại tập hợp sản phẩm mới (đã thêm/xóa/sửa dòng lẻ từ UI)
            for prod in products_list:
                if not prod.get("product_key"):
                    continue
                new_row = ComboDetail(
                    combo_variant_key=variant_key,
                    combo_composition_key=composition_key,
                    product_key=prod["product_key"],
                    product_price=prod["product_price"],
                    product_quantity=prod["product_quantity"],
                    created_date=current_time,
                    updated_date=current_time
                )
                self.session.add(new_row)
            
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            print(f"Lỗi khi cập nhật chi tiết combo: {e}")
            return False