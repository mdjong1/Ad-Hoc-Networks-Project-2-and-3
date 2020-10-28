import wsnsimpy.wsnsimpy_tk as wsp

simulator = wsp.Simulator(
    until=60,
    timescale=1,
    visual=True,
    terrain_size=(650, 650),
    title="MACAW Demo"
)

# define a line style for parent links
simulator.scene.linestyle("parent", color=(0, .7, 0), arrow="head", width=2)
