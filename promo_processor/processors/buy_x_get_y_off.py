from promo_processor.processor import PromoProcessor


class BuyGetDiscountProcessor(PromoProcessor):
    patterns = [
        r"Buy\s+(?P<quantity>\d+)\s+get\s+(?P<discount>\d+)%\s+off\b" 
    ]
    
    """
    sale_price : 10 * 2 = 20/2 = 10
    regular_price : 20
    volume_deals_description: Buy 2 get 50% off
    digital_coupon_price: Buy 2 get 50% off
    volume_deals_price : 10
    unit_price: volume_deals_price / quantity = 10/2 = 5
    digital_coupon_price
    """
    
    #"Buy 2 get 50% off"
    
    def calculate_deal(self, item, match):
        """Calculate promotion price for 'Buy X get Y% off' promotions."""
        
        item_data = item.copy()
        price = item_data.get("regular_price", 0)
        weight = item_data.get("weight")
        quantity = int(match.group('quantity'))
        discount_percentage = int(match.group('discount'))
        
        if weight:
            weight = float(weight.split()[0])
            volume_deals_price = price * weight * (1 - discount_percentage / 100)
            unit_price = volume_deals_price / weight
        else:
            volume_deals_price = price * quantity * (1 - discount_percentage / 100)
            unit_price = volume_deals_price / quantity
        
        item_data['volume_deals_price'] = round(volume_deals_price, 2)
        item_data['unit_price'] = round(unit_price, 2)
        item_data['digital_coupon_price'] = ""
 
        return item_data

    def calculate_coupon(self, item, match):
        """Calculate the final price after applying a coupon discount."""
        
        item_data = item.copy()
        
        price = item_data.get("regular_price", 0)
        weight = item_data.get("weight")
        quantity = int(match.group('quantity'))
        discount_percentage = int(match.group('discount'))
        
        if weight:
            volume_deals_price = price * weight * (1 - discount_percentage / 100)
            unit_price = volume_deals_price / weight
        else:
            volume_deals_price = price * quantity * (1 - discount_percentage / 100)
            unit_price = volume_deals_price / quantity

        item_data['digital_coupon_price'] = round(unit_price, 2)
        item_data['unit_price'] = round(unit_price, 2)
        
        return item_data