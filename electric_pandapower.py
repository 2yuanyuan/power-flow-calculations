import pandapower as pp


def create_power_system():
    """
    创建电力系统网络，包含发电机、负荷和线路。
    """
    # 创建空的 pandapower 网络
    net = pp.create_empty_network()

    # 创建母线 (buses)
    b1 = pp.create_bus(net, vn_kv=11, name="Bus 1")  # 电源1 (PV bus)
    b2 = pp.create_bus(net, vn_kv=11, name="Bus 2")  # 负荷1 (PQ bus)
    b3 = pp.create_bus(net, vn_kv=11, name="Bus 3")  # 负荷2 (PQ bus)
    b4 = pp.create_bus(net, vn_kv=11, name="Bus 4")  # 上级电网 (Slack bus)

    # 创建发电机 (gen)
    pp.create_gen(net, b1, p_mw=0.4889, vm_pu=1.05, name="Generator")

    # 创建负荷 (loads)
    pp.create_load(net, b2, p_mw=0.15, q_mvar=0.0493, name="Load 1")
    pp.create_load(net, b3, p_mw=0.15, q_mvar=0.0493, name="Load 2")

    # 创建外部电网 (ext_grid)
    pp.create_ext_grid(net, b4, vm_pu=1.02, va_degree=0, name="External Grid")

    # 基准阻抗计算
    base_voltage = 11  # kV
    base_power = 1  # MVA
    base_impedance = (base_voltage ** 2) / base_power  # 计算基准阻抗 (Ω)

    # 将阻抗标幺值转换为实际值
    r_per_km_pu = 0.09  # 标幺值
    x_per_km_pu = 0.1577  # 标幺值
    r_per_km = r_per_km_pu * base_impedance  # 实际值 (Ω/km)
    x_per_km = x_per_km_pu * base_impedance  # 实际值 (Ω/km)

    # 创建线路 (lines)
    pp.create_line_from_parameters(net, b1, b2, length_km=1, r_ohm_per_km=r_per_km, x_ohm_per_km=x_per_km,
                                   c_nf_per_km=0, max_i_ka=1)
    pp.create_line_from_parameters(net, b2, b3, length_km=1, r_ohm_per_km=r_per_km, x_ohm_per_km=x_per_km,
                                   c_nf_per_km=0, max_i_ka=1)
    pp.create_line_from_parameters(net, b3, b4, length_km=1, r_ohm_per_km=r_per_km, x_ohm_per_km=x_per_km,
                                   c_nf_per_km=0, max_i_ka=1)

    return net


# 创建电力系统
net = create_power_system()

# 运行潮流计算，设置更大的容差以放松收敛条件
pp.runpp(net, tolerance_mva=1e-3)  # 这里设置容差为0.1 MVA

# 输出潮流计算结果
print('潮流计算成功')
print('母线电压:')
for idx, bus in net.bus.iterrows():
    voltage_magnitude = net.res_bus.vm_pu.at[idx]
    voltage_angle = net.res_bus.va_degree.at[idx]
    print(f"节点 {bus['name']}: 电压幅值 = {voltage_magnitude:.4f} p.u., 电压相角 = {voltage_angle:.4f} 度")

# 输出各节点功率
print('节点功率:')
for idx, bus in net.bus.iterrows():
    p_mw = net.res_bus.p_mw.at[idx]
    q_mvar = net.res_bus.q_mvar.at[idx]
    print(f"节点 {bus['name']}: 有功功率 = {p_mw:.4f} MW, 无功功率 = {q_mvar:.4f} MVar")

# 输出线路的功率
print('线路功率:')
for idx, line in net.line.iterrows():
    p_from_mw = net.res_line.p_from_mw.at[idx]
    q_from_mvar = net.res_line.q_from_mvar.at[idx]
    p_to_mw = net.res_line.p_to_mw.at[idx]
    q_to_mvar = net.res_line.q_to_mvar.at[idx]
    print(f"线路 {line['name']} (从 {line['from_bus']} 到 {line['to_bus']}):")
    print(f"    从端有功功率 = {p_from_mw:.4f} MW, 从端无功功率 = {q_from_mvar:.4f} MVar")
    print(f"    到端有功功率 = {p_to_mw:.4f} MW, 到端无功功率 = {q_to_mvar:.4f} MVar")

# 判断功率守恒
total_gen_p = net.res_gen.p_mw.sum() + net.res_ext_grid.p_mw.sum()
total_load_p = net.res_load.p_mw.sum()
total_line_loss_p = (net.res_line.pl_mw.sum())

total_gen_q = net.res_gen.q_mvar.sum() + net.res_ext_grid.q_mvar.sum()
total_load_q = net.res_load.q_mvar.sum()
total_line_loss_q = (net.res_line.ql_mvar.sum())

print("\n功率守恒判断:")
print(f"总发电有功功率 = {total_gen_p:.4f} MW")
print(f"总负荷有功功率 = {total_load_p:.4f} MW")
print(f"总线路损耗有功功率 = {total_line_loss_p:.4f} MW")
print(f"功率平衡检查 (有功功率) = {total_gen_p:.4f} MW == {total_load_p + total_line_loss_p:.4f} MW")

print(f"总发电无功功率 = {total_gen_q:.4f} MVar")
print(f"总负荷无功功率 = {total_load_q:.4f} MVar")
print(f"总线路损耗无功功率 = {total_line_loss_q:.4f} MVar")
print(f"功率平衡检查 (无功功率) = {total_gen_q:.4f} MVar == {total_load_q + total_line_loss_q:.4f} MVar")

# 校验功率是否守恒
power_balance_p = abs(total_gen_p - (total_load_p + total_line_loss_p)) < 1e-3
power_balance_q = abs(total_gen_q - (total_load_q + total_line_loss_q)) < 1e-3

if power_balance_p and power_balance_q:
    print("功率守恒：是")
else:
    print("功率守恒：否")