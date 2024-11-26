from promo_processor.processor import PromoProcessor

class PricePerLbProcessor(PromoProcessor):
    """Processor for handling '$X/lb' type promotions."""

    patterns = [r'\$(?P<price_per_lb>\d+(?:\.\d{2})?)\/lb', r'\$(?P<price_per_lb>\d+\.\d{2})\/lb', r'\$(?P<price_per_lb>\d+\.\d{2})\s+per\s+lb\.\s+Limit\s+(?P<limit>\d+)-lbs\.']    
    
    
    
    def calculate_deal(self, item, match):
        """Process '$X/lb' type promotions for deals."""
        item_data = item.copy()
        price_per_lb = float(match.group('price_per_lb'))
        weight = item_data.get('weight', 1)
        limit = float(match.groupdict().get('limit', float('inf')))
        
        weight = weight.split("[")[0] if "[" in weight else weight.split()[0] if len(weight.split()) > 1 else weight
        weight = float(weight)
        
        if weight:
            if weight > limit and limit != float('inf'):
                total_price = (limit * price_per_lb) + ((weight - limit) * item_data.get('unit_price', price_per_lb))
            else:
                total_price = float(price_per_lb) * weight
            item_data["volume_deals_price"] = round(total_price, 2)
            item_data["unit_price"] = round(price_per_lb, 2)
            item_data["digital_coupon_price"] = ""
        return item_data


    def calculate_coupon(self, item, match):
        """Process '$X/lb' type promotions for coupons."""
        item_data = item.copy()
        price_per_lb = float(match.group('price_per_lb'))
        weight = item_data.get('weight', 1)
        limit = float(match.groupdict().get('limit', float('inf')))
        
        weight = float(weight)
        if weight > limit and limit != float('inf'):
            discount = price_per_lb * limit
        else:
            discount = price_per_lb * weight
            
        base_price = item_data.get('unit_price') or item_data.get("sale_price") or item_data.get("regular_price", 0)
            
        unit_price = round(float(base_price) - discount, 2)
        
        item_data["unit_price"] = unit_price
        item_data["digital_coupon_price"] = price_per_lb
        return item_data