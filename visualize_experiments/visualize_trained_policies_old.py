import os

import jax
from jax import numpy as jnp

from evosax import ParameterReshaper

from bsc_utils.miscellaneous import load_config_from_yaml
from bsc_utils.BrittleStarEnv import full_mjcf_configurations, create_environment, get_observation_space_dim_from_vectorized_env
from bsc_utils.controller import nn_controller
from bsc_utils.simulation import generate_video_joint_angle_raw
from bsc_utils.visualization import save_image_increasing_opacity_from_background_brittle_star_frames, plot_ip_oop_joint_angles, save_video_from_raw_frames
from bsc_utils.damage import check_damage

rng = jax.random.PRNGKey(0)

VIDEO_DIR = os.environ["VIDEO_DIR"]
IMAGE_DIR = os.environ["IMAGE_DIR"]
POLICY_PARAMS_DIR = os.environ["POLICY_PARAMS_DIR"]
RUN_NAME = os.environ["RUN_NAME"]

trained_policy_params = jnp.load(POLICY_PARAMS_DIR + RUN_NAME + ".npy")
config = load_config_from_yaml(POLICY_PARAMS_DIR + RUN_NAME + ".yaml")

# Generate normal morphologies
morphology_specification, arena_configuration, environment_configuration = full_mjcf_configurations(config["morphology"], config["arena"], config["environment"])

mjx_vectorized_env = create_environment(
                morphology_specification=morphology_specification,
                arena_configuration=arena_configuration,
                environment_configuration=environment_configuration,
                backend="MJX"
                )

# output dim necessary to instantiate the nn_model
rng, rng_input_dim = jax.random.split(rng, 2)
nn_input_dim = get_observation_space_dim_from_vectorized_env(mjx_vectorized_env, rng_input_dim, config["environment"]["sensor_selection"])
nn_output_dim = len(mjx_vectorized_env.actuators)

nn_controller = nn_controller(config, nn_output_dim)
nn_controller.model_from_config() # generates nn_controller.model attribute


rng, rng_input, rng_init = jax.random.split(rng, 3)
policy_params_init = nn_controller.model.init(rng_init, jax.random.uniform(rng_input, (nn_input_dim,)))
param_reshaper = ParameterReshaper(policy_params_init)

rng, rng_render = jax.random.split(rng, 2)
print("simulation of single episode started")

frames, joint_angles_ip, joint_angles_oop, background_frame, brittle_star_frames = generate_video_joint_angle_raw(
                                                                    policy_params_to_render=trained_policy_params,
                                                                    param_reshaper=param_reshaper,
                                                                    rng=rng_render,
                                                                    mjx_vectorized_env=mjx_vectorized_env,
                                                                    sensor_selection=config["environment"]["sensor_selection"],
                                                                    arm_setup=config["morphology"]["arm_setup"],
                                                                    nn_model=nn_controller.model,
                                                                    visualise_increasing_opacity=True
                                                                    )
print("simulation of single episode finished")

fig, axes = plot_ip_oop_joint_angles(joint_angles_ip, joint_angles_oop)

save_image_increasing_opacity_from_background_brittle_star_frames(
        background_frame=background_frame,
        brittle_star_frames=brittle_star_frames,
        number_of_frames= 8,
        file_path=None,
        show_image=True
)

# img = save_image_from_raw_frames(frames, 5, file_path=IMAGE_DIR + RUN_NAME + ".png", show_image=True)



# # Generate damaged morphologies
# config["damage"]["damage"] = True
# config["damage"]["arm_setup_damage"] = [5,0,5,0,5]
# check_damage(arm_setup = config["morphology"]["arm_setup"], arm_setup_damage = config["damage"]["arm_setup_damage"])

# morphology_specification_damage, arena_configuration, environment_configuration = full_mjcf_configurations(config["morphology"],
#                                                                                                     config["arena"],
#                                                                                                     config["environment"],
#                                                                                                     damage_cfg=config["damage"])

# mjx_vectorized_env_damage = create_environment(
#                 morphology_specification=morphology_specification_damage,
#                 arena_configuration=arena_configuration,
#                 environment_configuration=environment_configuration,
#                 backend="MJX"
#                 )


# rng, rng_render = jax.random.split(rng, 2)
# print("simulation of single episode started")

# frames, joint_angles_ip, joint_angles_oop, background_frame, brittle_star_frames = generate_video_joint_angle_raw(
#                                                                     policy_params_to_render=trained_policy_params,
#                                                                     param_reshaper=param_reshaper,
#                                                                     rng=rng_render,
#                                                                     mjx_vectorized_env=mjx_vectorized_env_damage,
#                                                                     sensor_selection=config["environment"]["sensor_selection"],
#                                                                     arm_setup=config["morphology"]["arm_setup"],
#                                                                     nn_model=nn_controller.model,
#                                                                     damage = True,
#                                                                     arm_setup_damage=[5,0,5,0,5],
#                                                                     visualise_increasing_opacity=True
#                                                                     )
# fig, axes = plot_ip_oop_joint_angles(joint_angles_ip, joint_angles_oop)

# save_image_increasing_opacity_from_background_brittle_star_frames(
#         background_frame=background_frame,
#         brittle_star_frames=brittle_star_frames,
#         number_of_frames= 8,
#         file_path=None,
#         show_image=True
# )

# # img = save_image_from_raw_frames(frames, 5, file_path=IMAGE_DIR + RUN_NAME + ".png", show_image=True)


