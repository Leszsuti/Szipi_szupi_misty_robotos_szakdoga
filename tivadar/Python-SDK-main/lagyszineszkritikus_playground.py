import gymnasium as gym
from stable_baselines3 import SAC
from stable_baselines3 import PPO
from tornaterem_playground import *
import cv2
from visualization import *
import torch
import keyboard

def main():
    env = MistyEnv()

    # model = SAC(
    #     "MlpPolicy",
    #     env,
    #     verbose=1,
    #     learning_rate=3e-4,
    #     buffer_size=50000,    # Mennyi múltbeli lépésre emlékezzen
    #     batch_size=128,        # Egyszerre hány mintát nézzen át
    #     tau=0.005,            # Célhálózat frissítési sebessége
    #     gamma=0.99,           # Jövőbeli jutalmak diszkontálása
    #     train_freq=1,         # Minden lépés után tanítson
    #     gradient_steps=2,     # Lépésenként hány optimalizációs lépést tegyen
    #     ent_coef='auto',      # Az entrópia (felfedezés) automatikus hangolása
    #       policy_kwargs=dict(
    #             net_arch=[128, 128]
    #       )
    # )
    model = SAC(
        "MlpPolicy",
        env,
        verbose=1,
    )
    # model = SAC.load("misty_sim", env=env)
    # model.load_replay_buffer("misty_sim_replay")
    while not env.playground_operator.command["started"]:
        time.sleep(0.1)
    # model.learn(total_timesteps=4000, log_interval=1)

    total_timesteps = 4000
    obs, _ = env.reset()
    model._setup_learn(
        total_timesteps=total_timesteps,
        callback=None,
        reset_num_timesteps=False,
        tb_log_name="SAC",
        progress_bar=False,
    )
    for i in range(total_timesteps):
        action, _ = model.predict(obs, deterministic=False)
        new_obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        model.replay_buffer.add(
            obs=obs,
            next_obs=new_obs,
            action=action,
            reward=np.array([reward], dtype=np.float32),
            done=np.array([done], dtype=np.float32),
            infos=[info]
        )
        obs = new_obs
        if done:
            obs, _ = env.reset()
        if model.num_timesteps > model.learning_starts:
            model.train(
                gradient_steps=1,
                batch_size=model.batch_size
            )
        model._update_current_progress_remaining(
            model.num_timesteps,
            total_timesteps
        )
        model.num_timesteps += 1
        if keyboard.is_pressed("q"):
            break

    # env.tivadar.stop_events()
    # env.tivadar.misty.stop()
    env.playground_operator.command["stop"] = True
    env.close()
    # cv2.destroyAllWindows()
    model.save("misty_sim")
    model.save_replay_buffer("misty_sim_replay")

if __name__ == "__main__":
    main()








