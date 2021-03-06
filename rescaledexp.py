
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensorflow.python.framework import ops
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import state_ops
from tensorflow.python.ops import variables
from tensorflow.python.ops import constant_op
from tensorflow.python.training import optimizer
from tensorflow.python.training import training_ops
import tensorflow as tf
import numpy as np

class RescaledExpOptimizer(optimizer.Optimizer):
  """Optimizer that implements the coordinate-wise rescapedexp algorithm.


  @@__init__
  """

  def __init__(self, learning_rate=1.0,epsilon=1e-8,
               use_locking=False, name="RescaledExp"):
    """Construct a new rescaledexp optimizer.
        learning_rate = scale factor to apply to FTRL regularization function.
        Default value of 1.0 achieves provably low regret in unconstrained
        problems.
    """
    super(RescaledExpOptimizer, self).__init__(use_locking, name)
    self._epsilon = epsilon
    self._lr = learning_rate

    self._k = np.sqrt(2)
    self._initialized = False

    # Tensor versions of the constructor arguments, created in _prepare().
    self._epsilon_t = None

  def _create_slots(self, var_list):
    for v in var_list:
        with ops.device(v.device):
            Gsq = constant_op.constant(self._epsilon,shape = v.get_shape())
            Gsum = constant_op.constant(0.0,shape = v.get_shape())
            L = constant_op.constant(0.0,shape = v.get_shape())
            M = constant_op.constant(0.0,shape = v.get_shape())
            center = constant_op.constant(0.0,shape = v.get_shape())
            initialized = constant_op.constant(0)
            old_var = constant_op.constant(0.0,shape=v.get_shape())
        self._get_or_make_slot(v,Gsq,"Gsq",self._name)
        self._get_or_make_slot(v,Gsum,"Gsum",self._name)
        self._get_or_make_slot(v,L,"L",self._name)
        self._get_or_make_slot(v,Gsq,"M",self._name)
        self._get_or_make_slot(v,center,"center",self._name)
        self._get_or_make_slot(v,initialized,"initialized",self._name)
        self._get_or_make_slot(v,old_var,"old_var",self._name)

  def _prepare(self):
    self._epsilon_t = ops.convert_to_tensor(self._epsilon, name="epsilon")

  def _apply_dense(self, grad, var):

      L = self.get_slot(var,"L")
      Gsq = self.get_slot(var,"Gsq")
      Gsum = self.get_slot(var,"Gsum")
      M = self.get_slot(var,"M")
      center = self.get_slot(var,"center")
      initialized = self.get_slot(var,"initialized")
      old_var = self.get_slot(var,"old_var")
      lr = self._lr


      epsilon_vector = constant_op.constant(self._epsilon,shape=var.get_shape())
      zero_vector = constant_op.constant(0.0,shape=var.get_shape())


      resets = tf.abs(grad)>2*L
      center_t_reset = tf.select(resets,old_var,center)
      center_t = tf.cond(tf.equal(initialized,0),lambda: var,lambda:\
              center_t_reset)

      k = self._k




      Gsq_t = Gsq+tf.square(grad)
      Gsum_t =Gsum+grad
      M_t = tf.maximum(M,tf.abs(Gsum_t)*L-Gsq_t)

      eta = lr*1.0/(k*tf.sqrt(2*(M_t+Gsq_t)))

      w_t = -tf.sign(Gsum_t)*(tf.exp(eta*tf.abs(Gsum_t))-1)

      Gsq_update = state_ops.assign(Gsq,tf.select(resets,epsilon_vector,Gsq_t))
      Gsum_update = state_ops.assign(Gsum,tf.select(resets,zero_vector,Gsum_t))
      M_update = state_ops.assign(M,tf.select(resets,zero_vector,M_t))

      L_update = state_ops.assign(L,tf.select(resets,tf.abs(grad),L))
      var_update = state_ops.assign(var,tf.select(resets,
          zero_vector,w_t)+center_t)
      #var_update =state_ops.assign(var,center_t)
      center_update = state_ops.assign(center,center_t)
      initialized_update = \
      state_ops.assign(initialized,constant_op.constant(1))
      old_var_update = state_ops.assign(old_var,var)

      return control_flow_ops.group(*[var_update,Gsq_update,Gsum_update,
                                        L_update,M_update,center_update,
                                        initialized_update,
                                        old_var_update])



  def _apply_sparse(self, grad, var):
    return self._appy_dense(grad,var)






class RescaledExpSphereOptimizer(optimizer.Optimizer):
  """Optimizer that implements the rescapedexp algorithm.


  @@__init__
  """

  def __init__(self, learning_rate=1.0,epsilon=1e-8,
               use_locking=False, name="RescaledExp"):
    """Construct a new rescaledexp optimizer.
        learning_rate = scale factor to apply to FTRL regularization function.
        Default value of 1.0 achieves provably low regret in unconstrained
        problems.
    """
    super(RescaledExpSphereOptimizer, self).__init__(use_locking, name)
    self._epsilon = epsilon
    self._lr = learning_rate

    self._k = np.sqrt(2)
    self._initialized = False

    # Tensor versions of the constructor arguments, created in _prepare().
    self._epsilon_t = None
    self._L = tf.Variable(0.0)
    self._step_count = tf.Variable(1.0)

  def _create_slots(self, var_list):
    for v in var_list:
        with ops.device(v.device):
            Gsq = constant_op.constant(self._epsilon)
            Gsum = constant_op.constant(0.0,shape = v.get_shape())
            L = constant_op.constant(0.0)
            M = constant_op.constant(0.0)
            center = constant_op.constant(0.0,shape = v.get_shape())
            initialized = constant_op.constant(0)
            step_accum = constant_op.constant(self._epsilon)
            old_var = constant_op.constant(0.0,shape=v.get_shape())
            step_count = constant_op.constant(1.0)
        self._get_or_make_slot(v,Gsq,"Gsq",self._name)
        self._get_or_make_slot(v,Gsum,"Gsum",self._name)
        self._get_or_make_slot(v,L,"L",self._name)
        self._get_or_make_slot(v,Gsq,"M",self._name)
        self._get_or_make_slot(v,center,"center",self._name)
        self._get_or_make_slot(v,initialized,"initialized",self._name)
        self._get_or_make_slot(v,step_accum,"step_accum",self._name)
        self._get_or_make_slot(v,old_var,"old_var",self._name)
        self._get_or_make_slot(v,step_count,"step_count",self._name)

  def _prepare(self):
    self._epsilon_t = ops.convert_to_tensor(self._epsilon, name="epsilon")


  def apply_gradients(self, grads_and_vars, global_step=None, name=None):
    """Apply gradients to variables.

    This is the second part of `minimize()`. It returns an `Operation` that
    applies gradients.

    Args:
      grads_and_vars: List of (gradient, variable) pairs as returned by
        `compute_gradients()`.
      global_step: Optional `Variable` to increment by one after the
        variables have been updated.
      name: Optional name for the returned operation.  Default to the
        name passed to the `Optimizer` constructor.

    Returns:
      An `Operation` that applies the specified gradients. If `global_step`
      was not None, that operation also increments `global_step`.

    Raises:
      TypeError: If `grads_and_vars` is malformed.
      ValueError: If none of the variables have gradients.
    """
    # This is a default implementation of apply_gradients() that can be shared
    # by most optimizers.  It relies on the subclass implementing the following
    # methods: _create_slots(), _prepare(), _apply_dense(), and _apply_sparse().
    grads_and_vars = tuple(grads_and_vars)  # Make sure repeat iteration works
    Gsum_sq = constant_op.constant(0.0)
    Gsq_sum = constant_op.constant(0.0)
    grad_norm_sq = constant_op.constant(0.0)
    for g, v in grads_and_vars:
      if not isinstance(g, (ops.Tensor, ops.IndexedSlices, type(None))):
        raise TypeError(
            "Gradient must be a Tensor, IndexedSlices, or None: %s" % g)
      if not isinstance(v, variables.Variable):
        raise TypeError(
            "Variable must be a tf.Variable: %s" % v)
      if g is not None:
        self._assert_valid_dtypes([g, v])
    var_list = [v for g, v in grads_and_vars if g is not None]
    if not var_list:
      raise ValueError("No gradients provided for any variable: %s" %
                       (grads_and_vars,))
    with ops.control_dependencies(None):
      self._create_slots(var_list)


    #update accumulators
    for grad,var in grads_and_vars:
      if grad is None:
          continue
      old_Gsum = self.get_slot(var,"Gsum")
      Gsum_sq += 2*tf.nn.l2_loss(old_Gsum+grad)

      grad_norm_sq += 2*tf.nn.l2_loss(grad)

      old_Gsq_sum = self.get_slot(var,"Gsq")
      Gsq_sum += old_Gsq_sum+2*tf.nn.l2_loss(grad)
    self._Gsum_sq = Gsum_sq
    self._Gsq_sum = Gsq_sum
    self._grad_norm_sq = grad_norm_sq
    step_count = self._step_count
    reset_L = tf.sqrt(grad_norm_sq)>2*self._L
#tf.logical_or(tf.sqrt(Gsq_sum/step_count)>2*self._L,
#                tf.sqrt(Gsq_sum/step_count)<0.5*self._L)

    update_L = state_ops.assign(self._L,tf.cond(reset_L,
                    lambda:tf.sqrt(grad_norm_sq),lambda:self._L))
    update_step_count = state_ops.assign(step_count,
            tf.cond(reset_L,lambda: constant_op.constant(1.0),lambda: step_count+1))


    tf.scalar_summary("rescaled exp: L",self._L)
    tf.scalar_summary("rescaled exp: RMS Gradient",tf.sqrt(Gsq_sum/step_count))
    tf.scalar_summary("rescaled exp: Gradient norm",tf.sqrt(grad_norm_sq))
    tf.scalar_summary("rescaled exp: step count",step_count)
    update_ops = [update_L,update_step_count]
    with ops.op_scope([], name, self._name) as name:
      self._prepare()
      for grad, var in grads_and_vars:
        if grad is None:
          continue
        # We colocate all ops created in _apply_dense or _apply_sparse
        # on the same device as the variable.
        with ops.name_scope("update_" + var.op.name), ops.colocate_with(var):#device(var.device):
          if isinstance(grad, ops.Tensor):
            update_ops.append(self._apply_dense(grad, var))
          else:
            update_ops.append(self._apply_sparse(grad, var))
      if global_step is None:
        return self._finish(update_ops, name)
      else:
        with ops.control_dependencies([self._finish(update_ops, "update")]):
            with ops.colocate_with(global_step):
                return state_ops.assign_add(global_step, 1, name=name).op

  def _apply_dense(self, grad, var):

      L = self.get_slot(var,"L")
      Gsq = self.get_slot(var,"Gsq")
      Gsum = self.get_slot(var,"Gsum")
      M = self.get_slot(var,"M")
      center = self.get_slot(var,"center")
      initialized = self.get_slot(var,"initialized")
      step_accum = self.get_slot(var,"step_accum")
      old_var = self.get_slot(var,"old_var")
      step_count = self.get_slot(var,"step_count")

      Gsum_sq = self._Gsum_sq
      Gsq_sum = self._Gsq_sum
      grad_norm_sq = self._grad_norm_sq
      lr = self._lr


      epsilon_t = self._epsilon_t
      zero_t = constant_op.constant(0.0)
      epsilon_vector = constant_op.constant(self._epsilon,shape=var.get_shape())
      zero_vector = constant_op.constant(0.0,shape=var.get_shape())


      #grad_norm_sq = tf.nn.l2_loss(grad)*2

      resets = tf.sqrt(grad_norm_sq)>2*L
#tf.logical_or(tf.sqrt(Gsq_sum/step_count)>2* \
#              L,tf.sqrt(Gsq_sum/step_count)<0.5*L)
      #reset_L=tf.logical_or(resets,grad_norm_sq<0.5*L**2)
      center_t_resets = tf.cond(resets,lambda: old_var,lambda:center)
      center_t = tf.cond(tf.equal(initialized,0),lambda: var,lambda:\
              center_t_resets)

      k = self._k

      Gsum_t_norm = tf.sqrt(Gsum_sq)



      Gsq_t = Gsq+grad_norm_sq
      Gsum_t =Gsum+grad

      #Gsum_t_norm = tf.sqrt(tf.nn.l2_loss(Gsum_t)*2)

      Gsum_t_normalized = Gsum_t/tf.maximum(Gsum_t_norm,epsilon_t)
      M_t = tf.maximum(M,Gsum_t_norm*L-Gsq_t)

      step_accum_t = tf.minimum(L*Gsum_t_norm,step_accum+Gsq_sum)

      #eta = lr*1.0/(k*tf.sqrt(2*(M_t+Gsq_t)))
      eta = lr*1.0/(k*tf.sqrt(2*step_accum_t))


      w_t = -Gsum_t_normalized*(tf.exp(eta*Gsum_t_norm)-1)

      Gsq_update = state_ops.assign(Gsq,tf.cond(resets,
        lambda:epsilon_t,lambda:Gsq_t))
      Gsum_update = state_ops.assign(Gsum,tf.cond(resets,
          lambda:zero_vector,lambda:Gsum_t))
      M_update = state_ops.assign(M,tf.cond(resets,
          lambda:zero_t,lambda:M_t))

      L_update = state_ops.assign(L,tf.cond(resets,
          lambda:tf.sqrt(grad_norm_sq),lambda:L))
      var_update = state_ops.assign(var,tf.cond(resets,
          lambda:zero_vector,lambda:w_t)+center_t)
      #var_update =state_ops.assign(var,center_t)
      center_update = state_ops.assign(center,center_t)
      initialized_update = \
      state_ops.assign(initialized,constant_op.constant(1))
      step_accum_update = state_ops.assign(step_accum,tf.cond(resets,
          lambda:epsilon_t,lambda:step_accum_t))
      old_var_update = state_ops.assign(old_var,var)
      step_count_update = state_ops.assign(step_count,tf.cond(resets,
          lambda:constant_op.constant(1.0),lambda:step_count+1))

      return control_flow_ops.group(*[var_update,Gsq_update,Gsum_update,
                                        L_update,M_update,center_update,
                                        initialized_update,step_accum_update,
                                        old_var_update,step_count_update])



  def _apply_sparse(self, grad, var):
    return self._appy_dense(grad,var)
