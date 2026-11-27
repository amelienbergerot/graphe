module Shop
  class Crate
    def initialize(items)
      @items = items
    end

    def weigh
      @items.size
    end

    def to_s
      "crate"
    end
  end

  class Ship < Crate
    def weigh
      super + 1
    end

    def self.build(n)
      Ship.new(n)
    end
  end
end
