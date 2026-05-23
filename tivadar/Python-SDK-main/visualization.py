import torch
import matplotlib.pyplot as plt

class Visualization:
    def neuron_activation_importance(self,model, obs):
        activations = {}

        def hook(name):
            def fn(module, input, output):
                activations[name] = output.detach().cpu()

            return fn

        handles = []
        for name, layer in model.named_modules():
            if isinstance(layer, torch.nn.Linear):
                handles.append(layer.register_forward_hook(hook(name)))

        model(obs)

        for h in handles:
            h.remove()

        return activations

    def plot_activations_heatmap(self,activations):
        for name, act in activations.items():
            act = act.squeeze().numpy()

            plt.figure()
            plt.title(name)
            plt.imshow(act.reshape(1, -1), aspect="auto")
            plt.colorbar()

        plt.show()
