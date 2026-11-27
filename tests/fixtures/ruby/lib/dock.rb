require_relative "shop"

def ship_all
  c = Shop::Ship.build(2)
  c.weigh
  report(c.to_s)
end

def report(text)
  puts text
end
