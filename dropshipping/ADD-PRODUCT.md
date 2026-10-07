# Adding a new product

It takes about 15 minutes: 👤 you find the product, 🤖 PowerShell Claude checks and lists it.

## 1. 👤 Find it
- From the 07:00 research, from the CJ app, or something you found yourself.
- Copy the **CJ link** or the **SKU**.

## 2. 🤖 Paste this into PowerShell Claude
Replace `PASTE CJ LINK OR SKU HERE`:

```
I want to add a new product to my Shopify store: PASTE CJ LINK OR SKU HERE
Follow CLAUDE.md. Don't publish or change prices without my OK.

1. CHECK first and show me a ✅/❌ list:
   - Cost (product + shipping) and my profit per order for US, CA and AU, using the same price rule as the agents (3× cost, at least $15 profit).
   - Shipping methods for US, CA and AU WITHOUT the "DDU" notice (customer must pay nothing extra), with delivery days. Is there US warehouse stock?
   - Not allowed: kids' products (no CPSIA certificates), brand copies, medical claims, weapons, batteries/liquids if they can't ship, anything that needs certificates.
   - Stock level and seller rating.
2. If it's OK and I say "add it":
   - Import it with the CJ app as a DRAFT, adults-only variants only.
   - Map every Shopify variant to the right CJ variant.
   - Add it to the agents' products table so /content works, and send /product SKU testing.
   - Write the product page: honest title, description and real delivery times, plus sizes from CJ. No fake reviews, discounts or countdowns.
3. Show me the draft. I approve, then you set it to Active.
```

## 3. 👤 Make videos
- Send `/content SKU` to the bot to get 5 video scripts.
- Make and post the videos.

## When an order comes
- In CJ, pick a shipping method **without** the yellow "DDU" box, then pay.
- If you're unsure, send Claude a screenshot first.
