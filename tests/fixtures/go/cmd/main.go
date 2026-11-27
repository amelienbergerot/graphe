package main

import "example.com/host/store"

func main() {
	c := store.NewCrate()
	c.Fill("tea")
	c.Weigh()
	c.Close()
	report()
}

func report() {}
