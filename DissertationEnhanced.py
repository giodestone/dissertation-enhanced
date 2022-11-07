from DissertationEnhancedLib.TrainingGraph import TrainingGraph
from DissertationEnhancedLib.PathGenerator import PathGenerator

def main():
    tg = TrainingGraph('way["highway"](56.459124,-2.985106,56.464221,-2.977424); (._;>;); out body;')
    #tg.show_graph()
    pg = PathGenerator(tg, regenerate_if_exists=True)
    pg.generate_training_data()


if __name__ == "__main__":
    main()
