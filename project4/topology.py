from mininet.topo import Topo

class LeafSpine( Topo ):
	def __init__( self ):

		# Initialize topology
		Topo.__init__( self )

		# Add hosts 
		h1 = self.addHost( 'h1' )
		h2 = self.addHost( 'h2' )
		h3  = self.addHost( 'h3' )
		h4  = self.addHost( 'h4' )
		h5 = self.addHost( 'h5' )
		h6 = self.addHost( 'h6' )


		# Add Spine Switches
		s4 = self.addSwitch( 's4' )
		s5 = self.addSwitch( 's5' )

		# Add Leaf Switches
		l1 = self.addSwitch( 'l1' )
		l2 = self.addSwitch( 'l2' )
		l3 = self.addSwitch( 'l3' )

		# Add links from spine to leaf switches
		self.addLink( s4, l1 )
		self.addLink( s4, l2 )
		self.addLink( s4, l3 )

		self.addLink( s5, l1 )
		self.addLink( s5, l2 )
		self.addLink( s5, l3 )

		#Add links from leaf switches to hosts
		self.addLink( l1, h1 )
		self.addLink( l1, h2 )

		self.addLink( l2, h3 )
		self.addLink( l2, h4 )

		self.addLink( l3, h5 )
		self.addLink( l3, h6 )



topos = { 'mytopo': ( lambda: LeafSpine() ) }