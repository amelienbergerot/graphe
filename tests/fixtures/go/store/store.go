package store

type Crate struct {
	items []string
}

type Ship struct {
	Crate
}

func NewCrate() *Crate {
	return &Crate{}
}

func (c *Crate) Fill(item string) {
	c.items = append(c.items, item)
}

func (c *Crate) Weigh() int {
	return len(c.items)
}

func (s *Ship) Weigh() int {
	return s.Crate.Weigh() + 1
}

func (c *Crate) Close() {}
